'''
Created on 13 sep. 2016

@author: Ruud
'''

from ply import lex, yacc
import datetime
import os
import sys


class XdrSyntaxError(SyntaxError):
    pass


class XdrLex:
    def __init__(self, *args, **kwargs):
        self.lexer = lex.lex(module=self, *args, **kwargs)
    
    def input(self, data):
        self.lexer.input(data)
    
    def token(self):
        t = self.lexer.token()
        print(t, file=sys.stderr)
        return t
    
    def __iter__(self):
        return self.lexer.__iter__()
    
    def __getattr__(self, name):
        return getattr(self.lexer, name)
    
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
        self.lexer.lineno += len(t.value)
        
    t_ignore = ' \t'
    
    def t_COMMENT(self, t):
        r'/\*(?:(?:.|\n)*?)\*/'
        self.lexer.lineno += t.value.count('\n')
    
    def t_error(self, t):
        line, column = self.get_line_info(t.lexpos)
        raise XdrSyntaxError("Invalid character at line {} '{}', position {}"
                             .format(self.lexer.lineno, line, column))
    
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
        self.lexer = XdrLex()
        self.symbols = {
            'unsigned int': 'type',
            'unsigned hyper': 'type',
            'int': 'type',
            'hyper': 'type',
            'enum': 'type',
            'bool': 'type',
            'opaque': 'type',
            'string': 'type',
            'struct': 'type',
            'union': 'type',
            'TRUE': 'enumerated value',
            'FALSE': 'enumerated value',
            }
        self.values = {
            'TRUE': 1,
            'FALSE': 0
            }
        self.union_types = {
            'unsigned int',
            'int',
            'bool',
            'enum',
            }
        self.scopes = []
        self.scope = None
    
    def parse(self, text, **kwargs):
        # Use the Xdr lexer
        kwargs['lexer'] = self.lexer
        return self.parser.parse(text, **kwargs)
    
    def get_source(self, p):
        start = p.lexpos(1)
        last = len(p) - 1
        finish = p.lexpos(last) + len(p[last])
        return p.lexer.lexdata[start:finish]

    def push_scope(self):
        self.scopes.append(set())
        self.scope = self.scopes[-1]
    
    def pop_scope(self):
        if not self.scopes:
            raise RuntimeError('Internal error: attempt to pop a scope from an empty scope list')
        
        self.scopes.pop()
        if self.scopes:
            self.scope = self.scopes[-1]
        else:
            self.scope = None
                                                                       
    def p_specification(self, p):
        '''specification : definition_list'''
        p[0] = Ast_Specification(None, p[1], lineno=p.lineno(1))
    
    def p_specification_empty(self, p):
        '''specification : empty'''
        p[0] = Ast_Specification(None, [], lineno=p.lineno(1))
    
    def p_definition_list_single(self, p):
        '''definition_list : definition'''
        p[0] = [p[1]]
    
    def p_definition_list_multi(self, p):
        '''definition_list : definition_list definition'''
        p[0] = p[1] + [p[2]]
    
    def p_new_type_name(self, p):
        '''new_type_name :'''
        name = p[-1]
        if name in self.symbols:
            raise XdrSyntaxError("Line {}: redefinition of name '{}'".format(p.lineno(0), name))
        self.symbols[name] = 'type'
        
    def p_new_const_name(self, p):
        '''new_const_name :'''
        name = p[-1]
        if name in self.symbols:
            raise XdrSyntaxError("Line {}: redefinition of name '{}'".format(p.lineno(0), name))
        self.symbols[name] = 'constant value'
        
    def p_new_enum_name(self, p):
        '''new_enum_name :'''
        name = p[-1]
        if name in self.symbols:
            raise XdrSyntaxError("Line {}: redefinition of name '{}'".format(p.lineno(0), name))
        self.symbols[name] = 'enumerated value'
        
    def p_definition_typedef(self, p):
        '''definition : TYPEDEF declaration ";"'''
        name = p[2].name
        if name:
            if str(name) in self.symbols:
                raise XdrSyntaxError("Line {}: redefinition of name '{}'".format(p.lineno(2), str(name)))
            self.symbols[str(name)] = 'type'
            if p[2].contents.name in self.union_types:
                self.union_types.add(str(name))
        p[0] = Ast_Definition(name, p[2], src=self.get_source(p), lineno=p.lineno(3))
    
    def p_definition_typedef_error(self, p):
        '''definition : TYPEDEF error ";"'''
        print("Line {}: syntax error".format(p.lineno(3)), file=sys.stderr)
    
    def p_defintion_structured(self, p):
        '''definition : ENUM IDENTIFIER new_type_name enum_body ";"
                      | STRUCT IDENTIFIER new_type_name struct_body ";"
                      | UNION IDENTIFIER new_type_name union_body ";"'''
        spec = p[4]
        spec.name = Ast_Ref(p[1], lineno=p.lineno(1))
        name = Ast_Name(p[2], lineno=p.lineno(2))
        if spec.name == 'enum':
            self.union_types.add(str(name))
        decl = Ast_Declaration(name, spec, lineno=p.lineno(4))
        p[0] = Ast_Definition(name, decl, src=self.get_source(p), lineno=p.lineno(5))
    
    def p_definition_structured_error(self, p):
        '''definition : ENUM IDENTIFIER error enum_body ";"
                      | STRUCT IDENTIFIER error struct_body ";"
                      | UNION IDENTIFIER error union_body ";"
                      | ENUM IDENTIFIER new_type_name error ";"
                      | STRUCT IDENTIFIER new_type_name error ";"
                      | UNION IDENTIFIER new_type_name error ";"'''
        print("Line {}: syntax error".format(p.lineno(5)), file=sys.stderr)
    
    def p_definition_constant(self, p):
        '''definition : CONST IDENTIFIER new_const_name "=" constant ";"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        self.values[str(name)] = int(p[5])
        p[0] = Ast_Constant(name, p[5], src=self.get_source(p), lineno=p.lineno(6))
    
    def p_definition_constant_error(self, p):
        '''definition : CONST IDENTIFIER error "=" constant ";"
                      | CONST IDENTIFIER new_const_name "=" error ";"'''
        print("Line {}: syntax error".format(p.lineno(3)), file=sys.stderr)
    
    def p_check_size(self, p):
        '''check_size :'''
        size = p[-1]
        if size is not None:
            if isinstance(size, Ast_Ref):
                if str(size) not in self.symbols:
                    raise XdrSyntaxError("Line {}: name '{}' used before it is defined"
                                         .format(size.lineno, str(size)))
                if self.symbols[str(size)] != 'constant value':
                    raise XdrSyntaxError("Line {}: named array size '{}' must refer to a named constant value, not '{}'"
                                         .format(size.lineno, str(size), self.symbols[str(size)]))
                int_size = self.values[str(size)]
            else:
                int_size = int(size)
            if not 0 <= int_size < 2**32:
                raise XdrSyntaxError("Line {}: array size must be between 0 and 2**32-1. Got '{}'"
                                     .format(size.lineno, int_size))
        
    def p_declaration_scalar(self, p):
        '''declaration : type_specification IDENTIFIER'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(name, p[1], lineno=p.lineno(2))
    
    def p_declaration_scalar_error(self, p):
        '''declaration : error IDENTIFIER'''
        print("Line {}: syntax error".format(p.lineno(2)), file=sys.stderr)
    
    def p_declaration_array_fixed(self, p):
        '''declaration : type_specification IDENTIFIER "[" value check_size "]"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(name, p[1], size=p[4], array=True, var=False, lineno=p.lineno(6))
    
    def p_declaration_array_fixed_error(self, p):
        '''declaration : error IDENTIFIER "[" value check_size "]"
                       | type_specification IDENTIFIER "[" error check_size "]"
                       | type_specification IDENTIFIER "[" value error "]"
                       | OPAQUE IDENTIFIER "[" error check_size "]"
                       | OPAQUE IDENTIFIER "[" value error "]"'''
        print("Line {}: syntax error".format(p.lineno(6)), file=sys.stderr)
    
    def p_declaration_array_var(self, p):
        '''declaration : type_specification IDENTIFIER "<" opt_value check_size ">"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(name, p[1], size=p[4], array=True, var=True, lineno=p.lineno(6))
    
    def p_declaration_array_var_error(self, p):
        '''declaration : error IDENTIFIER "<" opt_value check_size ">"
                       | type_specification IDENTIFIER "<" error check_size ">"
                       | type_specification IDENTIFIER "<" opt_value error ">"
                       | OPAQUE IDENTIFIER "<" error check_size ">"
                       | OPAQUE IDENTIFIER "<" opt_value error ">"
                       | STRING IDENTIFIER "<" error check_size ">"
                       | STRING IDENTIFIER "<" opt_value error ">"'''
        print("Line {}: syntax error".format(p.lineno(6)), file=sys.stderr)
    
    def p_declaration_opaque_fixed(self, p):
        '''declaration : OPAQUE IDENTIFIER "[" value check_size "]"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(name, Ast_Ref(p[1], lineno=p.lineno(1)), size=p[4], array=True, var=False, lineno=p.lineno(6))
    
    def p_declaration_opaque_var(self, p):
        '''declaration : OPAQUE IDENTIFIER "<" opt_value check_size ">"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(name, Ast_Ref(p[1], lineno=p.lineno(1)), size=p[4], array=True, var=True, lineno=p.lineno(6))
    
    def p_declaration_string(self, p):
        '''declaration : STRING IDENTIFIER "<" opt_value check_size ">"'''
        name = Ast_Name(p[2], lineno=p.lineno(2))
        p[0] = Ast_Declaration(name, Ast_Ref(p[1], lineno=p.lineno(1)), size= p[4], array=True, var=True, lineno=p.lineno(6))
    
    def p_declaration_optional(self, p):
        '''declaration : type_specification "*" IDENTIFIER'''
        name = Ast_Name(p[3], lineno=p.lineno(3))
        p[0] = Ast_Declaration(name, p[1], optional=True, lineno=p.lineno(3))
    
    def p_declaration_optional_error(self, p):
        '''declaration : error "*" IDENTIFIER'''
        print("Line {}: syntax error".format(p.lineno(2)), file=sys.stderr)
    
    def p_declaration_void(self, p):
        '''declaration : VOID'''
        p[0] = Ast_Declaration(None, None, lineno=p.lineno(1))
    
    def p_type_specification_unsigned(self, p):
        '''type_specification : UNSIGNED INT
                              | UNSIGNED HYPER'''
        uname = ' '.join((p[1], p[2]))
        name = Ast_Ref(uname, lineno=p.lineno(2))
        p[0] = Ast_TypeSpec(name, None, lineno=p.lineno(2))
    
    def p_type_specification_simple(self, p):
        '''type_specification : INT
                              | HYPER
                              | FLOAT
                              | DOUBLE
                              | QUADRUPLE
                              | BOOL'''
        name = Ast_Ref(p[1], lineno=p.lineno(1))
        p[0] = Ast_TypeSpec(name, None, lineno=p.lineno(1))
    
    def p_type_reference(self, p):
        '''type_ref : '''
        name = p[-1]
        if name not in self.symbols:
            raise XdrSyntaxError("Line {}: type name '{}' is not defined"
                                 .format(name.lineno, str(name)))
        if self.symbols[name] != 'type':
            raise XdrSyntaxError("Line {}: name '{}' must refer to a previously defined type, not '{)'"
                                 .format(name.lineno, str(name), self.symbols[name]))
        
    def p_type_specification_identifier(self, p):
        '''type_specification : IDENTIFIER type_ref'''
        name = Ast_Ref(p[1], lineno=p.lineno(1))
        p[0] = Ast_TypeSpec(name, None, lineno=p.lineno(1))

    def p_type_specification_enum(self, p):
        '''type_specification : ENUM enum_body'''
        p[0] = p[2]
        p[0].name = Ast_Ref(p[1], lineno=p.lineno(1))
    
    def p_type_specification_struct(self, p):
        '''type_specification : STRUCT struct_body'''
        p[0] = p[2]
        p[0].name = Ast_Ref(p[1], lineno=p.lineno(1))

    def p_type_specification_union(self, p):
        '''type_specification : UNION union_body'''
        p[0] = p[2]
        p[0].name = Ast_Ref(p[1], lineno=p.lineno(1))

    def p_enum_body(self, p):
        '''enum_body : "{" enum_const_list "}"'''
        p[0] = Ast_EnumBody(None, p[2], lineno=p.lineno(3))
    
    def p_enum_body_error(self, p):
        '''enum_body : "{" error "}"'''
        print("Line {}: syntax error".format(p.lineno(3)), file=sys.stderr)
    
    def p_enum_const_list_single(self, p):
        '''enum_const_list : enum_element'''
        p[0] = [p[1]]
    
    def p_enum_const_list_multi(self, p):
        '''enum_const_list : enum_const_list "," enum_element'''
        p[0] = p[1] + [p[3]]

    def p_check_enum_value(self, p):
        '''check_enum_value : '''
        value = p[-1]        
        if isinstance(value, Ast_Ref):
            int_value = self.values[value]
        else:
            int_value = int(value)
            
        if not -2**31 <= int_value < 2**31:
            raise XdrSyntaxError("Line {}: enumerated value must be between -2**31 and 2**31-1. Got {}"
                                 .format(value.lineno, int_value))

    def p_enum_element(self, p):
        '''enum_element : IDENTIFIER new_enum_name "=" value check_enum_value'''
        name = Ast_Name(p[1], lineno=p.lineno(1))
        p[0] = (name, p[4])

    def p_new_scope(self, p):
        '''new_scope :'''
        self.push_scope()
        
    def p_struct_body(self, p):
        '''struct_body : "{" new_scope declaration_list "}"'''
        p[0] = Ast_StructBody(None, p[3], lineno=p.lineno(4))
        self.pop_scope()
    
    def p_struct_body_error(self, p):
        '''struct_body : "{" new_scope error "}"'''
        print("Line {}: syntax error".format(p.lineno(3)), file=sys.stderr)
    
    def p_declaration_list_single(self, p):
        '''declaration_list : attribute_declaration ";"'''
        p[0] = [p[1]]
    
    def p_declaration_list_multi(self, p):
        '''declaration_list : declaration_list attribute_declaration ";"'''
        p[0] = p[1] + [p[2]]
    
    def p_attribute_declaration(self, p):
        '''attribute_declaration : declaration'''
        name = p[1].name
        if name:
            if name in self.scope:
                raise XdrSyntaxError("Line {}: redefinition of attribute name '{}'"
                                     .format(name.lineno, str(name)))
            self.scope.add(str(name))
        p[0] = p[1]
        
    def p_union_body(self, p):
        '''union_body : SWITCH new_scope "(" switch_declaration ")" "{" case_list opt_default "}"'''
        p[0] = Ast_UnionBody(None, [p[4], p[7], p[8]], lineno=p.lineno(9))
        self.pop_scope()
          
    def p_union_body_error(self, p):
        '''union_body : SWITCH new_scope "(" error ")" "{" case_list opt_default "}"
                      | SWITCH new_scope "(" switch_declaration ")" "{" error opt_default "}"
                      | SWITCH new_scope "(" switch_declaration ")" "{" case_list error "}"'''
        print("Line {}: syntax error".format(p.lineno(9)), file=sys.stderr)

    def p_switch_declaration(self, p):
        '''switch_declaration : attribute_declaration'''
        name = p[1].name
        if name not in self.union_types:
            raise XdrSyntaxError("Line {}: invalid type '{}' for union discriminator. Must be (unsigned) int or enum."
                                 .format(name.lineno, str(name)))
        p[0] = p[1]
    
    def p_case_list_single(self, p):
        '''case_list : case_spec'''
        p[0] = [p[1]]
    
    def p_case_list_multi(self, p):
        '''case_list : case_list case_spec'''
        p[0] = p[1] + [p[2]]
        
    def p_case_spec(self, p):
        '''case_spec : case_value_list attribute_declaration ";"'''
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
        '''opt_default : DEFAULT ":" attribute_declaration ";"'''
        p[0] = p[3]
        
    def p_value_constant(self, p):
        '''value : constant'''
        p[0] = p[1]
    
    def p_use_value(self, p):
        '''use_value : '''
        name = p[-1]
        if name not in self.symbols:
            raise XdrSyntaxError("Line {}: name '{}' not defined"
                                 .format(p.lineno(1), name))
        if self.symbols[name] not in ('enumerated value', 'constant value'):
            raise XdrSyntaxError("Line {}: name '{}' must refer to an integer value, not a {}"
                                 .format(p.lineno(1), name, self.symbols[name]))
            
    def p_value_identifier(self, p):
        '''value : IDENTIFIER use_value'''
        p[0] = Ast_Ref(p[1], lineno=p.lineno(1))
        
    def p_opt_value_empty(self, p):
        '''opt_value : empty'''
        p[0] = None
    
    def p_opt_value(self, p):
        '''opt_value : value'''
        p[0] = p[1]
    
    def p_constant_decimal(self, p):
        '''constant : DECIMAL'''
        p[0] = Ast_Value(p[1], int(p[1]), lineno=p.lineno(1))
    
    def p_constant_hexadecimal(self, p):
        '''constant : HEXADECIMAL'''
        p[0] = Ast_Value(p[1], int(p[1], base=16), lineno=p.lineno(1))
    
    def p_constant_octal(self, p):
        '''constant : OCTAL'''
        if p[1] == '0':
            p[0] = Ast_Value('0', 0, lineno=p.lineno(1))
        else:
            p[0] = Ast_Value('0o'+p[1].lstrip('0'), int(p[1], base=8), lineno=p.lineno(1))
    
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
        'void': 'xdr.Void',
        }
    
            
    def __init__(self, name=None, contents=None, **kwargs):
        self.name = name
        self.contents = contents
        for n, v in kwargs.items():
            setattr(self, n, v)
        self.imported_names = []
        self.exported_names = []
        
    @staticmethod
    def commentify(txt):
        return '\n'.join(('# ' + line) for line in txt.split('\n'))
    
    @staticmethod
    def indent(txt, step=4):
        return '\n'.join((' '*step + line) for line in txt.split('\n'))
    
    @staticmethod
    def check_redefinition(name, context):
        if str(name) in context['types'] or str(name) in context['constants']:
            raise XdrSyntaxError("Line {}: redefinition of name '{}'"
                                 .format(name.lineno, str(name)))
    
    @staticmethod
    def get_constant_value(name, context):
        if isinstance(name, Ast_Ref):
            v = context['constants'].get(str(name))
            if v is None:
                raise XdrSyntaxError("Line {}: constant value '{}' has not been defined"
                                     .format(name.lineno, str(name)))
        else:
            v = int(name)
        return v
    
    
class Ast_Specification(AstNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
                   
    def block(self):
        return '\n\n'.join(d.block() for d in self.contents)

    def validate(self):
        context = {'constants': {'FALSE': 0,
                                 'TRUE': 1
                                 },
                   'types': {'unsigned int': 'unsigned int',
                             'unsigned hyper': 'unsigned hyper',
                             'int': 'int',
                             'hyper': 'hyper',
                             'bool': 'bool',
                             'float': 'float',
                             'double': 'double',
                             'quadruple': 'quadruple',
                             'string': 'string',
                             'opaque': 'opaque',
                             'enum': Ast_EnumBody('enum', []),
                             'struct': Ast_StructBody('struct', []),
                             'union': Ast_UnionBody('union', [None, [], None]),
                             },
                  }
        for d in self.contents:
            d.validate(context)

class Ast_Definition(AstNode):
    def block(self):
        txt = ['']
        if self.src:
            txt.append(self.commentify(self.src))
        txt.append(self.contents.block())
        return '\n'.join(txt)
    
    def validate(self, context):
        self.check_redefinition(self.contents.name, context)
        context['types'][str(self.contents.name)] = self.contents
        self.contents.validate(context)


class Ast_Constant(AstNode):
    def block(self):
        txt = ['']
        if self.src:
            txt.append(self.commentify(self.src))
        txt.append("{} = {}".format(str(self.name), str(self.contents)))
        return '\n'.join(txt)
    
    def validate(self, context):
        self.check_redefinition(self.name, context)
        context['constants'][str(self.name)] = int(self.contents)


class Ast_Declaration(AstNode):
    def __init__(self, *args, **kwargs):
        self.optional = False
        self.var = None
        self.size = None
        super().__init__(*args, **kwargs)

    def basetype(self, name):
        if name == 'string':
            base = 'xdr.String'
        elif self.var is not None:
            if self.var:
                base = 'xdr.Var'
            else:
                base = 'xdr.Fixed'
            if name == 'opaque':
                base += 'Opaque'
            else:
                base += 'Array'
        else:
            base = self.typemap.get(str(name), name)
        return base
        
    def block(self):
        txt = ['']
        if self.contents is not None:
            if self.optional:
                txt.append("@Optional")
            name = str(self.contents.name)
            txt.append("class {}({}):".format(str(self.name), self.basetype(name)))
            if self.var is not None:
                txt.append(self.indent("size = {}".format(self.size)))
                if name not in ('string', 'opaque'):
                    txt.append(self.indent("type = {}".format(self.contents.inline())))
            else:
                if name in ('enum', 'struct', 'union'):
                    txt.append(self.indent(self.contents.block()))
                else: 
                    txt.append(self.indent("pass"))
            return '\n'.join(txt)
        else:
            return ''
    
    def inline(self):
        txt = []
        if self.contents is None:
            return ('None', 'None')
        name = str(self.contents.name)
        if self.var is not None:
            txt.append("{}(".format(self.basetype(name)))
            txt.append("size={}".format(self.size))
            if name not in ('string', 'opaque'):
                txt.append(", type={}".format(self.typemap.get(name, name)))
            txt.append(")")
            txt = ''.join(txt)
        else:
            if name in ('enum', 'struct', 'union'):
                txt.append("{}(".format(self.typemap.get(name, name)))
                txt.append(self.indent(self.contents.inline()))
                txt.append(")")
            else: 
                txt.append(self.typemap.get(name, name))
            txt = '\n'.join(txt)
        if self.optional:
            txt="xdr.Optional({})".format(txt)
        return str(self.name), txt
    
    def validate(self, context):
        if self.size is not None:
            value = self.get_constant_value(self.size, context)
            if not 0 <= value < 2**32:
                raise XdrSyntaxError("Line {}: invalid array size: '{}' ({})"
                                     .format(self.size.lineno, str(self.size), value))
        if self.contents:
            if isinstance(self.contents, Ast_Ref):
                name = str(self.contents)
                if name not in context['types']:
                    raise XdrSyntaxError("Line {}: type named '{}' used before it has been defined"
                                         .format(self.contents.lineno, name))
            else:
                self.contents.validate(context)
                
        
class Ast_TypeSpec(AstNode):
    def block(self):
        return "pass"

    def inline(self):
        name = str(self.name)
        return self.typemap.get(name, name)
    
    def validate(self, context):
        if not str(self.name) in context['types']:
            raise XdrSyntaxError("Line {}: type '{}' used before it is defined."
                                 .format(self.name.lineno, str(self.name)))


class Ast_EnumBody(Ast_TypeSpec):
    def _body_to_str(self):
        return ("{} = {}".format(str(n), str(v)) for n, v in self.contents)
    
    def block(self):
        return '\n'.join(self._body_to_str())

    def inline(self):
        return ',\n'.join(self._body_to_str())

    def validate(self, context):
        super().validate(context)
        for n, v in self.contents:
            self.check_redefinition(n, context)
            value = self.get_constant_value(v, context)
            context['constants'][str(n)] = value
            
class Ast_StructBody(Ast_TypeSpec):
    def _body_to_str(self):
        return ("{} = {}".format(*decl.inline())
                for decl in self.contents if decl is not None)
    
    def block(self):
        return '\n'.join(self._body_to_str())

    def inline(self):
        return ',\n'.join(self._body_to_str())

    def validate(self, context):
        super().validate(context)
        attributes = set()
        for decl in self.contents:
            attr = decl.name
            if attr is not None:
                if str(attr) in attributes:
                    raise XdrSyntaxError("Line {}: redefinition of struct member '{}'"
                                         .format(attr.lineno, str(attr)))
                attributes.add(str(attr))
            decl.validate(context)

class Ast_UnionBody(Ast_TypeSpec):
    def _body_to_str(self):
        txt = []
        switch, cases, default = self.contents
        txt.append("switch = ({}, {})".format(*switch.inline()))
        
        c_list = []
        for cvl, decl in cases:
            if len(cvl) == 1:
                cv_str = str(cvl[0])
            else:
                cv_str = "(" + ', '.join(str(c) for c in cvl) + ")"
            d_name, d_typ = decl.inline()
            c_list.append("{}: ({}, {})".format(cv_str, d_name, d_typ))
        txt.append('case = {\n' + self.indent(',\n'.join(c_list)) + '\n}')
        
        if default:
            txt.append("default = ({}, {})".format(*default.inline()))
        return txt
    
    def block(self):
        return "\n".join(self._body_to_str())

    def inline(self):
        return ",\n".join(self._body_to_str())

    def validate(self, context):
        super().validate(context)
        switch, cases, default = self.contents
        attributes = set()
        case_values = set()
        attributes.add(str(switch.name))
        switch.validate(context)
        for cv_list, decl in cases:
            for case in cv_list:
                value = self.get_constant_value(case, context)
                case_values.add(value)
            attr = decl.name
            if attr:
                if str(attr) in attributes:
                    raise XdrSyntaxError("Line {}: redefinition of union member '{}'"
                                         .format(attr.lineno, str(attr)))
                attributes.add(str(attr))
            if decl:
                decl.validate(context)
        if default:
            attr = default.name
            if attr:
                if str(attr) in attributes:
                    raise XdrSyntaxError("Line {}: redefinition of union member '{}'"
                                         .format(attr.lineno, str(attr)))
                attributes.add(str(attr))
            default.validate(context)
            
    
class Ast_Name(AstNode):
    def __eq__(self, other):
        return self.name == other
    
    def __str__(self):
        return self.name
    
    def __hash__(self):
        return self.name.__hash__()
    

class Ast_Ref(AstNode):
    def __eq__(self, other):
        return self.name == other
    
    def __str__(self):
        return self.name
    
    def __hash__(self):
        return self.name.__hash__()


class Ast_Value(AstNode):
    def __str__(self):
        return self.name
    
    def __int__(self):
        return self.contents


class XdrCompile:
    def __init__(self, source):
        self.source = source
        parser = XdrYacc()
        with open(source) as f:
            self.result = parser.parse(f.read())
        self.timestamp = datetime.datetime.now()
        self.result.validate()
    
    def write(self, destination):
        with open(destination, "w") as f:
            f.write(self.generate())
    
    def generate(self):
        if not isinstance(self.result, Ast_Specification):
            raise SyntaxError("Compilation of '{}' failed".format(self.source))
        
        
        msg = ["# Generated on {:s} from {:s}".format(str(self.timestamp), os.path.abspath(self.source)),
               "#",
               "# Any manual changes in this file will be lost when the file is regenerated",
               "#",
               "# This file includes the contents of the source file as comments.",
               "# Each definition from the source file is followed by the corresponding Python code.",
               "#",
               "#",
               "import xdrlib2.xdr_types as xdr"
               ""
               ]
        msg.append(self.result.block())
        msg.append("")
        msg.append("")
        msg.append('# End of generated code\n')
        return "\n".join(msg)
                   
if __name__ == "__main__":
#     lexer = XdrLex()
#     with open('../etc/example.xdr') as f:
#         lexer.input(f.read())
#     for token in lexer:
#         print(token)
    import logging
    logging.basicConfig(
        level = logging.DEBUG,
        filename = 'xdr_parse.log',
        filemode = 'w',
        format = "%(filename)10s:%(lineno)4d:%(message)s"
        )
    parser = XdrYacc(debug=True)
    with open('../etc/example.xdr') as f:
        text  = f.read().splitlines()
    
    log = logging.getLogger()
    result = parser.parse('\n'.join(text[0:25]), debug=log)
    print(result)
    
    
#     with open('../etc/example.xdr') as f:
#         result = parser.parse(f.read())
#     print(result)
        
# #     print(XdrCompile('../etc/example.xdr').generate())
#     print(XdrCompile('../etc/stress.xdr').generate())
    
    
