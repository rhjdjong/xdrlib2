'''
Created on 13 sep. 2016

@author: Ruud
'''

from ply import lex, yacc
import datetime
import os


class XdrSyntaxError(SyntaxError):
    pass


class XdrLex:
    def __init__(self, *args, **kwargs):
        self.lexer = lex.lex(module=self, *args, **kwargs)
        self.lineno = 1
    
    def input(self, data):
        self.lexer.input(data)
    
    def token(self):
        return self.lexer.token()
    
    def __iter__(self):
        return self.lexer.__iter__()
    
    
    # These are the XDR keywords, as per section
    # 6.4 (Syntax Notes) of the XDR specification
    reserved = {
        'bool': 'BOOL',
        'case': 'CASE',
        'const': 'CONST',
        'default': 'DEFAULT',
        'double': 'DOUBLE',
        'quadruple': 'QUADRUPLE',
        'enum': 'ENUM',
        'float': 'FLOAT',
        'hyper': 'HYPER',
        'int': 'INT',
        'opaque': 'OPAQUE',
        'string': 'STRING',
        'struct': 'STRUCT',
        'switch': 'SWITCH',
        'typedef': 'TYPEDEF',
        'union': 'UNION',
        'unsigned': 'UNSIGNED',
        'void': 'VOID',
        }
    
    tokens = (
        'IDENTIFIER',
        'DECIMAL',
        'HEXADECIMAL',
        'OCTAL',
        ) + tuple(reserved.values())

    literals = (
        '[', ']',
        '<', '>',
        '{', '}',
        '(', ')',
        '*',
        '=',
        ',',
        ';',
        ':',    
        )
    
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z][a-zA-Z0-9_]*'
        t.type = self.reserved.get(t.value, 'IDENTIFIER')
        return t
    
    t_DECIMAL = r'-?[1-9][0-9]*'
    t_HEXADECIMAL = r'0x[0-9a-fA-F]+'
    t_OCTAL = r'0[0-7]*'
    
    def t_newline(self, t):
        r'\n+'
        self.lineno += len(t.value)
        
    t_ignore = ' \t'
    
    def t_COMMENT(self, t):
        r'/\*(?:(?:.|\n)*?)\*/'
        pass
    
    def t_error(self, t):
        line, column = self.get_line_info(t.lexpos)
        raise XdrSyntaxError("Invalid character at line {} '{}', position {}"
                             .format(self.lineno, line, column))
    
    def get_line_info(self, position):
        last_cr = self.lexer.lexdata.rfind('\n', 0, position)
        if last_cr < 0:
            last_cr = 0
        column = position - last_cr
        next_cr = self.lexer.lexdata.find('\n', last_cr)
        if next_cr < 0:
            line = self.lexer.lexdata[last_cr:]
        else:
            line = self.lexer.lexdata[last_cr:next_cr]
        return line, column
    

class XdrYacc:
    tokens = XdrLex.tokens
    literals = XdrLex.literals
    
    start = 'specification'
    
    def __init__(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)
        self.lexer = XdrLex().lexer
        
#         self.globals = {
#             'bool': 'type',
#             'double': 'type',
#             'quadruple': 'type',
#             'enum': 'type',
#             'float': 'type',
#             'hyper': 'type',
#             'int': 'type',
#             'opaque': 'type',
#             'string': 'type',
#             'struct': 'type',
#             'union': 'type',
#             'unsigned int': 'type',
#             'unsigned hyper': 'type',
#             'void': 'type',
#             'TRUE': 'value',
#             'FALSE': 'value',
#             }
#         self.scopes = [self.globals]
        
    def parse(self, text, **kwargs):
        # Use the Xdr lexer
        kwargs['lexer'] = self.lexer
        return self.parser.parse(text, **kwargs)
    
#     def push_scope(self):
#         self.scopes.append({})
#     
#     def pop_scope(self):
#         self.scopes.pop()
#     
#     def new_name(self, name, use, lineno):
#         scope = self.scopes[-1]
#         if name in scope:
#             raise XdrSyntaxError("Duplicate name '{}' on line {}"
#                                  .format(name, lineno))
#         scope[name] = use
#     
#     def use_name(self, name, use, lineno):
#         for scope in self.scopes:
#             if name in scope:
#                 if scope[name] != use:
#                     raise XdrSyntaxError("Line {}: name '{}' is a {}. Expected a {}"
#                                          .format(lineno, name, scope[name], use))
#                 break
#         else:
#             raise XdrSyntaxError("Name '{}' on line {} used but not defined"
#                                  .format(name, lineno))
            
    
    
    def get_source(self, p):
        start = p.lexpos(1)
        last = len(p) - 1
        finish = p.lexpos(last) + len(p[last])
        return p.lexer.lexdata[start:finish]
                                                                       
    def p_specification(self, p):
        '''specification : definition_list'''
        p[0] = Ast_Specification(p[1], None, lineno=p.lineno(1))
    
    def p_specification_empty(self, p):
        '''specification : empty'''
        p[0] = Ast_Specification([], None, lineno=p.lineno(1))
    
    def p_definition_list_single(self, p):
        '''definition_list : definition'''
        p[0] = [p[1]]
    
    def p_definition_list_multi(self, p):
        '''definition_list : definition_list definition'''
        p[0] = p[1] + [p[2]]
    
    def p_definition_typedef(self, p):
        '''definition : TYPEDEF declaration ";"'''
        decl = p[2]
        decl.__type__ = Ast_DeclarationTypeDef
        p[0] = Ast_Definition(decl, None, src=self.get_source(p), lineno=p.lineno(3))
    
    def p_defintion_structured(self, p):
        '''definition : ENUM IDENTIFIER enum_body ";"
                      | STRUCT IDENTIFIER struct_body ";"
                      | UNION IDENTIFIER union_body ";"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        spec = Ast_TypeSpec(p[3], Ast_Name(p[1], lineno=p.lineno(1)), lineno=p.lineno(3))
        p[0] = Ast_Definition(spec, name, src=self.get_source(p), lineno=p.lineno(4))
    
    def p_definition_constant(self, p):
        '''definition : CONST IDENTIFIER "=" constant ";"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Constant(p[4], name, src=self.get_source(p), lineno=p.lineno(5))
    
    def p_declaration_scalar(self, p):
        '''declaration : type_specification IDENTIFIER'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(p[1], name, lineno=p.lineno(2))
    
    def p_declaration_array_fixed(self, p):
        '''declaration : type_specification IDENTIFIER "[" value "]"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(p[1], name, size=p[4], array=True, var=False, lineno=p.lineno(5))
    
    def p_declaration_array_var(self, p):
        '''declaration : type_specification IDENTIFIER "<" opt_value ">"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(p[1], name, size=p[4], array=True, var=True, lineno=p.lineno(5))
    
    def p_declaration_opaque_fixed(self, p):
        '''declaration : OPAQUE IDENTIFIER "[" value "]"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(p[1], name, size=p[4], array=True, var=False, lineno=p.lineno(5))
    
    def p_declaration_opaque_var(self, p):
        '''declaration : OPAQUE IDENTIFIER "<" opt_value ">"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(p[1], name, size=p[4], array=True, var=True, lineno=p.lineno(5))
    
    def p_declaration_string(self, p):
        '''declaration : STRING IDENTIFIER "<" opt_value ">"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(p[1], name, size= p[4], array=True, var=True, lineno=p.lineno(5))
    
    def p_declaration_optional(self, p):
        '''declaration : type_specification "*" IDENTIFIER'''
        name = Ast_Name(p[3], lineno=p.lineno(3))
        p[0] = Ast_Declaration(p[1], name, optional=True, lineno=p.lineno(3))
    
    def p_declaration_void(self, p):
        '''declaration : VOID'''
        name = Ast_Name(None, lineno=p.lineno(1))
        p[0] = Ast_Declaration(None, name, lineno=p.lineno(1))
    
    def p_type_specification_unsigned(self, p):
        '''type_specification : UNSIGNED INT
                              | UNSIGNED HYPER'''
        name = Ast_Name(' '.join((p[1], p[2])), lineno=p.lineno(2))
        p[0] = Ast_TypeSpec(None, name, lineno=p.lineno(2))
    
    def p_type_specification_simple(self, p):
        '''type_specification : INT
                              | HYPER
                              | FLOAT
                              | DOUBLE
                              | QUADRUPLE
                              | BOOL
                              | IDENTIFIER'''
        name = Ast_Name(p[1], lineno=p.lineno(1))
        p[0] = Ast_TypeSpec(None, name, lineno=p.lineno(2))
    
    def p_type_specification_strucutured(self, p):
        '''type_specification : ENUM enum_body
                              | STRUCT struct_body
                              | UNION union_body'''
        name = Ast_Name(p[1], lineno=p.lineno(1))
        p[0] = Ast_TypeSpec(p[2], name, lineno=p.lineno(2))
    
    def p_enum_body(self, p):
        '''enum_body : "{" enum_const_list "}"'''
        p[0] = p[2]
    
    def p_enum_const_list_single(self, p):
        '''enum_const_list : enum_element'''
        p[0] = [p[1]]
    
    def p_enum_const_list_multi(self, p):
        '''enum_const_list : enum_const_list "," enum_element'''
        p[0] = p[1] + [p[3]]
        
    def p_enum_element(self, p):
        '''enum_element : IDENTIFIER "=" value'''
        name = Ast_Name(p[1], lineno=p.lineno(1))
        p[0] = Ast_EnumDef(p[3], p[1], lineno=p.lineno(1))
    
    def p_struct_body(self, p):
        '''struct_body : "{" declaration_list "}"'''
        p[0] = p[2]
    
    def p_declaration_list_single(self, p):
        '''declaration_list : declaration ";"'''
        p[0] = [p[2]]
    
    def p_declaration_list_multi(self, p):
        '''declaration_list : declaration_list declaration ";"'''
        p[0] = p[1] + [p[2]]
    
    def p_union_body(self, p):
        '''union_body : SWITCH "(" declaration ")" "{" case_list opt_default "}"'''
        p[0] = [p[3], p[6], p[7]]
    
    def p_case_list_single(self, p):
        '''case_list : case_spec'''
        p[0] = p[1]
    
    def p_case_list_multi(self, p):
        '''case_list : case_list case_spec'''
        p[0] = p[1] + p[2]
        
    def p_case_spec(self, p):
        '''case_spec : case_value_list declaration ";"'''
        p[0] = [p[1], p[2]]
    
    def p_case_value_list_single(self, p):
        '''case_value_list : case_value'''
        p[0] = [p[1]]
    
    def p_case_value_list_multi(self, p):
        '''case_value_list : case_value_list case_value'''
        p[0] = p[1] + [p[2]]
    
    def p_case_value(self, p):
        '''case_value : CASE value ":"'''
        p[0] = p[2]
    
    def p_opt_default_empty(self, p):
        '''opt_default : empty'''
        p[0] = None
    
    def p_opt_default_present(self, p):
        '''opt_default : DEFAULT ":" declaration ";"'''
        p[0] = p[3]
        
    def p_value_constant(self, p):
        '''value : constant'''
        p[0] = p[1]
    
    def p_value_identifier(self, p):
        '''value : IDENTIFIER'''
        p[0] = Ast_Name(p[1], lineno=p.lineno(1))
        
    def p_opt_value_empty(self, p):
        '''opt_value : empty'''
        p[0] = None
    
    def p_opt_value(self, p):
        '''opt_value : value'''
        p[0] = p[1]
    
    def p_constant_decimal(self, p):
        '''constant : DECIMAL'''
        p[0] = p[1]
    
    def p_constant_hexadecimal(self, p):
        '''constant : HEXADECIMAL'''
        p[0] = p[1]
    
    def p_constant_octal(self, p):
        '''constant : OCTAL'''
        p[0] = '0o'+p[1].lstrip('0')
    
    def p_empty(self, p):
        'empty :'
        pass

    def p_error(self, p):
        if p:
            msg = "Syntax error at '{}' in line {}".format(p.value, p.lineno)
        else:
            msg = "Syntax error at EOF'"
        raise XdrSyntaxError(msg)

    
class AstNode:
    xdr_globals = {'unsigned int': 'type',
                   'unsigned hyper': 'type',
                   'int': 'type',
                   'hyper': 'type',
                   'float': 'type',
                   'double': 'type',
                   'quadruple': 'type',
                   'enum': 'type',
                   'struct': 'type',
                   'union': 'type',
                   'opaque': 'type',
                   'string': 'type',
                   'bool': 'type',
                   'TRUE': 'value',
                   'FALSE': 'value',
                   }
    
    typemap = {
        'unsigned int': 'xdr.Int32u',
        'unsigned hyper': 'xdr.Int64u',
        'int': 'xdr.Int32',
        'hyper': 'xdr.Int64',
        'float': 'xdr.Float32',
        'double': 'xdr.Float64',
        'quadruple': 'xdr.Float128',
        'bool': 'xdr.Boolean',
        'string': 'xdr.String',
        'enum': 'xdr.Enumeration',
        'struct': 'xdr.Structure',
        'union': 'xdr.Union',
        }
    
            
    def __init__(self, contents=None, name=None, **kwargs):
        self.contents = contents
        self.name = name
        for n, v in kwargs:
            setattr(self, n, v)
        
    @staticmethod
    def commentify(txt):
        return '\n'.join(('# ' + line) for line in txt.split('\n'))
    
    @staticmethod
    def indent(txt, step=4):
        return '\n'.join((' '*step + line) for line in txt.split('\n'))
    
    

class Ast_Specification(AstNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        spec_globals = {}
        for definition in self.contents:
            for name, typ in definition.exported_names:
                if name in spec_globals:
                    raise XdrSyntaxError("Line {}: duplicate name '{}'"
                                         .format(name.lineno, name))
                spec_globals[str(name)] = typ
        
        for definition in self.contents:
            for name, expected_type in definition.imported_names:
                actual_type = spec_globals.get(name)
                if not actual_type:
                    actual_type = self.xdr_globals.get(name)
                if not actual_type:
                    raise XdrSyntaxError("Line {}: referenced name '{:s}' is not defined"
                                         .format(name.lineno, name))
                if actual_type != expected_type:
                    raise XdrSyntaxError("Line {}: referenced name '{}' is a {}, expected a {}"
                                         .format(name.lineno, name, actual_type, expected_type))
                   
    def __str__(self):
        return '\n\n'.join(d.block() for d in self.contents)


class Ast_Definition(AstNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exported_names = self.contents.exported_names[:]
        if self.name:
            self.exported_names.append((self.name, 'type'))
        self.imported_names = self.contents.imported_names[:]
        
    def block(self):
        txt = []
        if self.src:
            txt.append(self.commentify(self.src))
        txt.append(self.contents.block())
        return '\n'.join(txt)


class Ast_Constant(AstNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exported_names = [(self.name, 'value')]
        self.imported_names = []
        
    def block(self):
        txt = []
        if self.src:
            txt.append(self.commentify(self.src))
        txt.append("{:s} = {:s}".format(self.name, self.contents))
        return '\n'.join(txt)


class Ast_Declaration(AstNode):
    def __init__(self, *args, **kwargs):
        self.optional = False
        self.var = None
        self.size = None
        super().__init__(*args, **kwargs)
        
        self.exported_names.extend(self.contents.exported_names)
        self.imported_names = self.contents.imported_names[:]

    def inline(self):
        txt = []
        if self.var is not None:
            txt.append("{:s}(".format(self.contents.basetype()))
            txt.append("size={:s}".format(self.size))
            if self.contents.name not in ('string', 'opaque'):
                txt.append(", type={:s}".format(self.typemap(self.contents.name)))
            txt.append(")")
            txt = ''.join(txt)
        else:
            if self.contents.name in ('enum', 'struct', 'union'):
                txt.append("{:s}(".format(self.contents.basetype))
                txt.append(self.indent(self.contents.inline()))
                txt.append(")")
            else: 
                txt.append(self.contents.basetype)
            txt = '\n'.join(txt)
        if self.optional:
            txt="xdr.Optional({:s})".format(txt)
        return self.name, txt
                
    
class Ast_DeclarationTypeDef(Ast_Declaration):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        if self.name:
            self.exported_names.append((self.name, 'type'))
        
    def block(self):
        txt = []
        if self.optional:
            txt.append("@Optional")
        txt.append("class {:s}({:s}):".format(self.name, self.contents.basetype()))
        txt.append(self.indent(self.contents.block()))
        return '\n'.join(txt)
    
    def inline(self):
        return "{:s} = {:s}".format(super().inline())
        

class Ast_TypeSpec(AstNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exported_names = []
        if self.name:
            self.imported_names = [(self.name, 'type')]
        else:
            self.imported_names = []
        
        if self.name == 'enum':
            for enum_def in self.contents:
                self.exported_names.extend(enum_def.exported_names)
                self.imported_names.extend(enum_def.imported_names)
        elif self.name == 'struct':
            members = set()
            for decl in self.contents:
                if decl.name:
                    if decl.name in members:
                        raise XdrSyntaxError("Line {}: duplicate struct member name '{}'"
                                             .format(decl.name.lineno, decl.name))
                    members.add(str(decl.name))
                self.exported_names.extend(decl.exported_names)
                self.imported_names.extend(decl.imported_names)
        elif self.name == 'union':
            switch, case_list, default = self.contents
            if not switch.name:
                raise XdrSyntaxError("Line {}: union discriminator must have an integral type"
                                     .format(switch.leaf.lineno))
            members = set(switch.name)
            self.exported_names.extend(switch.contents.exported_names)
            self.imported_names.extend(switch.contents.imported_names)
            for case_values, case_decl in case_list:
                if case_decl.name and case_decl.name in members:
                    raise XdrSyntaxError("Line {}: duplicate union member name '{}'"
                                         .format(case_decl.name.lineno, case_decl.name))
                members.add(case_decl.name)
                self.exported_names.extend(case_decl.contents.exported_names)
                self.imported_names.extend(case_decl.contents.imported_names)
                for cv in case_values:
                    if isinstance(cv, Ast_Name):
                        self.imported_names.append(cv, 'value')
            if default:
                if default.name:
                    if default.name in members:
                        raise XdrSyntaxError("Line {}: duplicate union member name '{}'"
                                             .format(default.name.lineno, default.name))
                    members.add(default.name)
                self.exported_names.extend(default.contents.exported_names)
                self.imported_names.extend(default.contents.imported_names)
        else:
            pass
            
    def basetype(self):
        if self.name == 'string':
            base = 'xdr.String'
        elif self.var is not None:
            if self.var:
                base = 'xdr.Var'
            else:
                base = 'xdr.Fixed'
            if self.name == 'opaque':
                base += 'Opaque'
            else:
                base += 'Array'
        else:
            base = self.typemap.get(self.name)
        return base
                
    
    def block(self):
        txt = []
        if self.name == 'enum':
            for e_def in self.contents:
                txt.append(e_def.block())
        elif self.name == 'struct':
            for decl in self.contents:
                txt.append("{:s} = {:s}".format(decl.inline()))
        elif self.name == 'union':
            switch, cases, default = self.contents
            txt.append("switch = ({:s}, {:s})".format(switch.inline()))
            txt.append("case = {")
            for cv, decl in cases:
                if len(cv) == 1:
                    txt.append(self.indent("{:s}:".format(cv)))
                else:
                    txt.append(self.indent("({:s}):".format(',\n '.join(str(c) for c in cv))))
                txt.append(self.indent(self.indent("({:s}, {:s}),"
                                                   .format(decl.inline()))))
            txt.append("}")
            if default:
                txt.append("default = ({:s}, {:s})".format(default.inline()))
        else:
            txt.append("pass")
        return "\n".join(txt)

    def inline(self):
        txt = []
        basetype = self.basetype()
        if self.var is not None:
            txt.append("{:s}(".format(basetype))
            txt.append(self.indent("size={:s}".format(self.size)))
            if self.name not in ('string', 'opaque'):
                txt.append(self.indent())
            if self.contents is None:
                return basetype
        else:
            if self.name == 'enum':
                pass
            elif self.name == 'struct':
                pass
            elif self.name == 'union':
                pass
            else:
                if self.optional:
                    msg = "Optional({:s})".format(self.name)
                else:
                    msg = "{:s}".format(self.name)
                txt.append("{:s}".format(basetype))
        txt = '\n'.join(txt)
        if self.optional:
            txt = "Optional({:s})".format(txt)
        return txt
                
                
            
class Ast_EnumDef(AstNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exported_names = [(self.name, 'value')]
        if isinstance(self.contents, Ast_Name):
            self.imported_names = [(self.contents, 'value')]
        else:
            self.imported_names = []
            
    def block(self):
        return "{:s} = {:s}".format(self.name, self.contents)
    
    def inline(self):
        return "{:s}={:s}".format(self.name, self.contents)
    
    
class Ast_Name(str):
    def __new__(cls, txt, lineno=None):
        obj = super().__new__(cls, txt)
        obj.lineno = lineno
        return obj

        
            

class XdrCompile:
    def __init__(self, source):
        self.source = source
        parser = XdrYacc()
        with open(source) as f:
            self.result = parser.parse(f.read())
        self.timestamp = datetime.datetime.now()
        self.identifiers = []
    
    def write(self, destination):
        with open(destination, "w") as f:
            f.write(self.generate())
    
    def generate(self):
        if not isinstance(self.result, Ast_Specification):
            raise SyntaxError("Compilation of '{}' failed".format(self.source))
        
        
        msg = ["# Generated on {}s from {}".format(self.timestamp, self.source),
               "#",
               "# Any manual changes in this file will be lost when the file is regenerated",
               "#",
               "# This file includes the contents of the source file as comments.",
               "# Following each definition from the source file is the corresponding Python definition",
               "#",
               "#",
               "from xdrlib2.xdr_types import *"
               ""
               ]
        msg.append(str(self.result))
        msg.append['\n\n']
        msg.append['# End of generated code\n']
        return "\n".join(msg)
                   
if __name__ == "__main__":
#     lexer = XdrLex()
#     with open('../etc/example.xdr') as f:
#         lexer.input(f.read())
#     for token in lexer:
#         print(token)
    
#     parser = XdrYacc(debug=True)
#     with open('../etc/example.xdr') as f:
#         result = parser.parse(f.read())
#     print(result)
        
    XdrCompile('../etc/example.xdr')
    
