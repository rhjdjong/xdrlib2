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
        self.assertTrue(issubclass(ns['MyInt'], xdr.OptionalCls))
    
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

    def test_union(self):
        txt = "union A switch (int s) { case 1: void; case 2: string creator<10>; case 3: int a[3]; };"
        result = self.parser.parse(txt)
        ns = {}
        exec(result, ns)
        A = ns['A']
        a1 = A(1, None)
        a2 = A(2, b"me")
        a3 = A(3, [0, 1, 2])
        self.assertEqual(a1, (1, None))
        self.assertEqual(a2, (2, b"me"))
        self.assertEqual(a3, (3, [0, 1, 2]))
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()