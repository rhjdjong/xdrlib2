'''
Created on 21 sep. 2016

@author: Ruud
'''
import unittest
from xdrlib2 import xdr_parser
import xdrlib2.xdr_types as xdr

xdr_constant_def = """
/* random comment */
const A = 1;
const B = -2;
const C = 0xa;
const D = 010;
"""

xdr_enum_def = """
/* enum definition */
enum Enum_A {
    RED = 1,
    YELLOW = 2
};
"""

xdr_struct_def = """
/*
 * A complete file:
 */
const MAXUSERNAME = 32;     /* max length of a user name */
const MAXFILELEN = 65535;   /* max length of a file      */
const MAXNAMELEN = 255;     /* max length of a file name */

struct file {
    string filename<MAXNAMELEN>; /* name of file    */
    string owner<MAXUSERNAME>;   /* owner of file   */
    opaque data<MAXFILELEN>;     /* file data       */
};
"""
class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = xdr_parser.Parser()

    def test_error_at_eof(self):
        self.assertRaisesRegex(SyntaxError, "Syntax error at EOF", self.parser.parse, "const A = 10")
           
    def test_constant_def(self):
        result = self.parser.parse(xdr_constant_def)
        ns = {}
        exec(result, ns)
        self.assertEqual(ns['A'], 1)
        self.assertEqual(ns['B'], -2)
        self.assertEqual(ns['C'], 10)
        self.assertEqual(ns['D'], 8)
           
    def test_constant_name_must_be_unique(self):
        text = xdr_constant_def + "\nconst A = 3;"
        self.assertRaisesRegex(SyntaxError, "redefinition of name 'A'", self.parser.parse, text)
           
    def test_constant_cannot_have_negative_hexadecimal_or_octal_value(self):
        text = ["const A = -0xa;", "const B = -010;"]
        for t in text:
            self.assertRaisesRegex(SyntaxError, "invalid character '-'", self.parser.parse, t)
       
    def test_constant_def_cannot_refer_to_named_constant(self):
        text = ["const A = 10;", "const B = A;"]
        self.assertRaisesRegex(SyntaxError, "syntax error at 'A'", self.parser.parse, '\n'.join(text))
       
    def test_enum_definition(self):
        result = self.parser.parse(xdr_enum_def)
        ns = {}
        exec(result, ns)
        self.assertEqual(ns['RED'], 1)
        self.assertEqual(ns['YELLOW'], 2)
        self.assertTrue(issubclass(ns['Enum_A'], xdr.Enumeration))
       
    def test_enum_definition_cannot_override_const_definition(self):
        txt = "const RED = 10;\n" + xdr_enum_def
        self.assertRaisesRegex(SyntaxError, "redefinition of name 'RED'", self.parser.parse, txt)
       
    def test_enum_names_do_not_leak_into_calling_environment(self):
        result = self.parser.parse(xdr_enum_def)
        ns = {}
        exec(result, ns)
        with self.assertRaises(NameError):
            RED  # @UndefinedVariable
               
    def test_enum_values_can_be_defined_constant(self):
        txt = "const A = 10;\nconst B = -20;\nenum Enum_B { X = A, Y = B };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        self.assertEqual(ns['X'], ns['A'])
        self.assertEqual(ns['Y'], ns['B'])
       
    def test_enum_values_range(self):
        result = self.parser.parse("enum EnumX { MIN = -2147483648, MAX = 2147483647 };")
        ns = {}
        exec(result, ns)
        self.assertEqual(ns['MIN'], xdr.Int32._min)  # @UndefinedVariable
        self.assertEqual(ns['MAX'], xdr.Int32._max-1)  # @UndefinedVariable
   
        for t in ["enum EnumA { A = " + str(xdr.Int32._min - 1) + "};",  # @UndefinedVariable
                  "enum EnumB { B = " + str(xdr.Int32._max) + "};"]:  # @UndefinedVariable
            with self.assertRaisesRegex(SyntaxError, 'enumerated value'):
                result = self.parser.parse(t)
                print(result)
           
    def test_struct_definition(self):
        result = self.parser.parse(xdr_struct_def)
        ns = {}
        exec(result, ns)
        self.assertTrue(issubclass(ns['file'], xdr.Structure))
   
    def test_struct_cannot_shadow_global_name(self):
        txt = "const X = 10;\nstruct MyStruct { int a; float b; bool X; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of specification-global', self.parser.parse, txt)
       
    def test_struct_cannot_have_duplicate_attributes(self):
        txt = "struct MyStruct { int a; float b; bool a; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of attribute', self.parser.parse, txt)
       
    def test_different_structs_can_have_identically_named_attributes(self):
        txt = "struct A { int a; float b; };\nstruct B { bool x; bool a; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        a_instance = eval("A(1, 2.0)", ns)
        b_instance = eval("B(True, False)", ns)
        self.assertEqual(a_instance.a, 1)
        self.assertEqual(b_instance.a, False)
           
    def test_union(self):
        txt = "union A switch (int s) { case 1: void; case 2: string creator<10>; case 3: int a[3]; default: float d; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a1 = A(1, None)
        a2 = A(2, b"me")
        a3 = A(3, [0, 1, 2])
        a4 = A(4, 1.5)
        self.assertEqual(a1, (1, None))
        self.assertEqual(a2, (2, b"me"))
        self.assertEqual(a3, (3, [0, 1, 2]))
        self.assertEqual(a4, (4, 1.5))
      
    def test_union_case_declaration_can_have_multiple_case_values(self):
        txt = "union A switch (int s) { case 1: void; case 2: case 3: string creator<10>; case 4: case 5: case 6: int a[3]; default: float d; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a1 = A(1, None)
        a2 = A(2, b"me")
        a3 = A(3, b"you")
        a4 = A(4, [0, 1, 2])
        a5 = A(5, [4, 5, 6])
        a6 = A(6, [7, 8, 9])
        a7 = A(7, 1.5)
          
        self.assertEqual(a1, (1, None))
        self.assertEqual(a2, (2, b"me"))
        self.assertEqual(a3, (3, b"you"))
        self.assertEqual(a4, (4, [0, 1, 2]))
        self.assertEqual(a5, (5, [4, 5, 6]))
        self.assertEqual(a6, (6, [7, 8, 9]))
        self.assertEqual(a7, (7, 1.5))
          
    def test_union_switch_type_can_be_derived_int_type(self):
        txt = "typedef unsigned int myint; union A switch ( myint s) { case 1: int a; case 2: float b; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a1 = A(1, 10)
        self.assertIsInstance(a1[0], ns['myint'])
           
    def test_union_switch_type_can_be_derived_enum_type(self):
        txt = "enum myenum {x=10, y=20}; union A switch ( myenum s) { case x: int a; case y: float b; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a1 = A(ns['x'], 100)
        self.assertIsInstance(a1[0], ns['myenum'])
      
    def test_union_discriminator_name_cannot_shadow_global_name(self):
        txt = "enum myenum {x=10, y=20}; union A switch ( myenum x) { case y: int a; default: float b; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of specification-global', self.parser.parse, txt)
      
    def test_union_case_name_cannot_shadow_global_name(self):
        txt = "enum myenum {x=10, y=20}; union A switch ( myenum a) { case x: int y; default: float b; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of specification-global', self.parser.parse, txt)
          
    def test_union_default_name_cannot_shadow_global_name(self):
        txt = "enum myenum {x=10, y=20}; union A switch ( myenum a) { case x: int b; default: float y; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of specification-global', self.parser.parse, txt)
  
    def test_union_case_name_cannot_match_discriminator_name(self):
        txt = "union A switch ( int a) { case 1: int a; default: float b; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of attribute', self.parser.parse, txt)
          
    def test_union_case_name_cannot_match_other_case_name(self):
        txt = "union A switch ( int a) { case 1: int b; case 2: case 3: double c; case 4: float b; default: float d; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of attribute', self.parser.parse, txt)
          
    def test_union_default_name_cannot_match_discriminator_name(self):
        txt = "union A switch ( int a) { case 1: int b; default: float a; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of attribute', self.parser.parse, txt)
          
    def test_union_default_name_cannot_match_other_case_name(self):
        txt = "union A switch ( int a) { case 1: int b; case 2: case 3: double c; case 4: float d; default: float d; };"
        self.assertRaisesRegex(SyntaxError, 'redefinition of attribute', self.parser.parse, txt)
  
    def test_different_unions_can_have_attributes_with_same_name(self):
        txt = "union A switch (int s) { case 1: int a; case 2: bool b;}; union B switch (int b) { case TRUE: float a; case FALSE: string s<>; };" 
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        B = ns['B']
        a1 = A(1, 7)
        a2 = A(2, True)
        b1 = B(True, 1.5)
        b2 = B(False, b'hi')
        self.assertEqual(a1, (1, 7))
        self.assertEqual(a2, (2, True))
        self.assertEqual(b1, (True, 1.5))
        self.assertEqual(b2, (False, b'hi'))
  
    def test_typedef_simple_alias(self):
        txt = "typedef int MyInt;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        self.assertTrue(issubclass(ns['MyInt'], xdr.Int32))
       
    def test_typedef_simple_optional(self):
        txt = "typedef int * MyInt;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        self.assertTrue(issubclass(ns['MyInt'], xdr.Int32))
        self.assertTrue(issubclass(ns['MyInt'], xdr.Optional))
       
    def test_typedef_simple_type_fixed_array(self):
        txt = "const SIZE=20;\ntypedef int iarr[10];\ntypedef float farr[SIZE];"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        iarr = ns['iarr']
        farr = ns['farr']
        self.assertEqual(iarr._size, 10)
        self.assertEqual(iarr._type, xdr.Int32)
        self.assertEqual(farr._size, 20)
        self.assertEqual(farr._type, xdr.Float32)
           
    def test_typedef_simple_type_var_array(self):
        txt = "const SIZE=20;\ntypedef int iarr<10>;\ntypedef float farr<SIZE>;\ntypedef bool barr<>;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        iarr = ns['iarr']
        farr = ns['farr']
        barr = ns['barr']
        self.assertEqual(iarr._size, 10)
        self.assertEqual(iarr._type, xdr.Int32)
        self.assertEqual(farr._size, 20)
        self.assertEqual(farr._type, xdr.Float32)
        self.assertEqual(barr._size, xdr.Int32u._max - 1)  # @UndefinedVariable
       
    def test_named_array_size_must_be_a_defined_constant(self):
        txt = "const A = 10;\ntypedef int barr[AA];"
        self.assertRaisesRegex(SyntaxError, 'name .* not defined', self.parser.parse, txt)
   
    def test_named_array_size_must_not_be_negative(self):
        txt = "const A = -10;\ntypedef int barr[A];"
        self.assertRaisesRegex(SyntaxError, 'size must be between', self.parser.parse, txt)
       
    def test_array_size_cannot_be_larger_than_unsigned_integer(self):
        txt = "typedef int arr[" + str(xdr.Int32u._max) + "];"  # @UndefinedVariable
        self.assertRaisesRegex(SyntaxError, 'size must be between', self.parser.parse, txt)
       
    def test_array_can_have_size_0(self):
        txt = "typedef int a[0];\ntypedef int b<0>;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        a = ns['a']
        b = ns['b']
        self.assertEqual(a._size, 0)
        self.assertEqual(b._size, 0)
       
    def test_opaque_and_string(self):
        txt = "typedef opaque a[10];\ntypedef opaque b<20>;\ntypedef string c<>;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        a = ns['a']
        b = ns['b']
        c = ns['c']
        self.assertTrue(issubclass(a, xdr.FixedOpaque))
        self.assertEqual(a._size, 10)
        self.assertTrue(issubclass(b, xdr.VarOpaque))
        self.assertEqual(b._size, 20)
        self.assertTrue(issubclass(c, xdr.String))
        self.assertEqual(c._size, xdr.Int32u._max-1)  # @UndefinedVariable
      
    def test_typedef_void(self):
        txt = "typedef void;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        self.assertSetEqual({'xdr', 'TRUE', 'FALSE', '__builtins__'}, set(ns.keys()))
        self.assertIn("# typedef void", result)
   
    def test_empty_specification(self):
        txt = ""
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        self.assertSetEqual({'xdr', 'TRUE', 'FALSE', '__builtins__'}, set(ns.keys()))
 
    def test_enum_definition_via_typedef(self):
        txt = "typedef enum { a = 1, b = 2 } myenum;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        self.assertTrue(issubclass(ns['myenum'], xdr.Enumeration))
        self.assertEqual(ns['a'], 1)
        self.assertEqual(ns['b'], 2)

    def test_struct_definition_via_typedef(self):
        txt = "typedef struct { int a; float b; bool *c; } A;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        self.assertTrue(issubclass(A, xdr.Structure))
        x = A(1, 2.5, None)
        y = A(2, 0.5, True)
        self.assertEqual(x.a, 1)
        self.assertEqual(x.b, 2.5)
        self.assertEqual(x.c, None)
        self.assertEqual(y.a, 2)
        self.assertEqual(y.b, 0.5)
        self.assertEqual(y.c, True)
        
    def test_union_definition_via_typedef(self):
        txt = "typedef union switch(unsigned int s){ case 0: int a; case 1: float *b; default: bool *c; } A;"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        self.assertTrue(issubclass(A, xdr.Union))
        a = A(0, 100)
        b = A(1, None)
        c = A(1, 0.5)
        d = A(2, True)
        e = A(3, None)
        self.assertEqual(a, (0, 100))
        self.assertEqual(b, (1, None))
        self.assertEqual(c, (1, 0.5))
        self.assertEqual(d, (2, True))
        self.assertEqual(e, (3, None))

    def test_inline_enum_definition(self):
        txt = "struct A { enum { a = 1, b = 2 } x; enum { c = 3, d = 4 } y[5]; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a = ns['a']
        b = ns['b']
        c = ns['c']
        d = ns['d']
        x = A(1, [3, 4, 3, 3, 4])
        self.assertEqual(a, 1)
        self.assertEqual(b, 2)
        self.assertEqual(x.x, 1)
        self.assertEqual(x.y, [c, d, c, c, d])
        
    def test_inline_struct_definition(self):
        txt = "struct A { struct { int x; float *b; bool c<10>; } x; int b; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a = A((3, None, (True, False, True)), 5)
        self.assertEqual(a.x.x, 3)
        self.assertEqual(a.x.b, None)
        self.assertSequenceEqual(a.x.c, (True, False, True))
        self.assertEqual(a.b, 5)
        
    def test_inline_union_definition(self):
        txt = "struct A { union switch (int s) {case 1: bool a; case 2: float c;} u; int v;};"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a = A((1, True), 5)
        b = A((2, 0.5), 6)
        self.assertEqual(a.u, (1, True))
        self.assertEqual(a.v, 5)
        self.assertEqual(b.u, (2, 0.5))
        self.assertEqual(b.v, 6)
    
    def test_struct_with_void_elements(self):
        txt = "struct A { int x; void; int y; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a = A(1, 2)
        self.assertEqual(a.x, 1)
        self.assertEqual(a.y, 2)

    def test_inline_struct_with_void_elements(self):
        txt = "struct A { struct {int x; void; int y; } p; int q;};"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a = A((1, 2), 3)
        self.assertEqual(a.p.x, 1)
        self.assertEqual(a.p.y, 2)
        self.assertEqual(a.q, 3)
        
    def test_struct_with_single_element(self):
        txt = "struct A { int x; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a = A(3)
        self.assertEqual(a.x, 3)

    def test_embeded_struct_with_single_element(self):
        txt = "struct A { struct { int x; } p; float q;};"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a = A(3, 2.5)
        self.assertEqual(a.p.x, 3)
        self.assertEqual(a.q, 2.5)
        
    def test_struct_with_single_void_element(self):
        txt = "struct A { void; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        self.assertTrue(issubclass(A, xdr.Structure))
        with self.assertRaises(NotImplementedError):
            A()

    def test_embeded_struct_with_single_void_element(self):
        txt = "union U switch (int s) { case 1: struct { void; } x; default: int y;};"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['U']
        self.assertTrue(issubclass(A, xdr.Union))
        self.assertRaises(NotImplementedError, A, 1, None)
        a = A(2, 3)
        self.assertEqual(a, (2, 3))


        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()