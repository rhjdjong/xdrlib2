'''
Created on 8 okt. 2016

@author: Ruud
'''
import unittest
import math
import sys

import xdrlib2 as xdr

class TestIntegers(unittest.TestCase):
    def test_default_instantiation(self):
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            with self.subTest(integer_type=integer_type):
                self.assertEqual(integer_type(), 0)


    def test_integer_type_accepts_values_in_range(self):
        value_set = {xdr.Int32: (-2**31, -1024, 0, 123456, 2**31-1),
                     xdr.Int32u: (0, 123456, 2**31, 2**32-1),
                     xdr.Int64: (-2**63, -2**33, 0, 123456, 2**31, 2**63-1),
                     xdr.Int64u: (0, 123456, 2**32, 2**63, 2**64-1)}
        
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            for value in value_set[integer_type]:
                with self.subTest(integer_type=integer_type, value=value):
                    self.assertEqual(integer_type(value), value)
    
    def test_integer_type_does_not_accept_values_out_of_range(self):
        value_set = {xdr.Int32: (-2**31-1, 2**31),
                     xdr.Int32u: (-1, 2**32),
                     xdr.Int64: (-2**63-1, 2**63),
                     xdr.Int64u: (-1, 2**64)}
        
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            for value in value_set[integer_type]:
                with self.subTest(integer_type=integer_type, value=value):
                    self.assertRaises(ValueError, integer_type, value)
    
    def test_integer_type_can_be_instantiated_with_string(self):
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            for args, value in ((("16", 10), 16),
                                (("32",), 32),
                                (("abcd", 16), 0xabcd),
                                (("765", 8), 0o765)):
                with self.subTest(integer_type=integer_type, args=args, value=value):
                    self.assertEqual(integer_type(*args), value)
    

class TestBaseEnumerations(unittest.TestCase):
    def test_base_enumeration_cannot_be_instantiated(self):
        with self.assertRaises(NotImplementedError):
            _ = xdr.Enumeration()


class TestDerivedEnumeration(unittest.TestCase):
    class MyEnum(xdr.Enumeration):
        RED = 2
        YELLOW = 3
        BLUE = 5
    
    FileKind = xdr.Enumeration.typedef(TEXT=0, DATA=1, EXEC=2)
    
    def test_names_are_in_global_namespace(self):
        self.assertEqual(TEXT, 0) # @UndefinedVariable
        self.assertEqual(DATA, 1) # @UndefinedVariable
        self.assertEqual(EXEC, 2) # @UndefinedVariable
        self.assertEqual(RED, 2) # @UndefinedVariable
        self.assertEqual(YELLOW, 3) # @UndefinedVariable
        self.assertEqual(BLUE, 5) # @UndefinedVariable
        self.assertIsInstance(RED, self.MyEnum) # @UndefinedVariable
        self.assertIsInstance(DATA, self.FileKind) # @UndefinedVariable
    
    def test_enum_default_values_is_first_defined_value(self):
        self.assertEqual(self.MyEnum(), 2)
        if sys.version_info.major > 3 or (sys.version_info.major == 3 and
                                          sys.version_info.minor >= 6):
            # As of version 3.6 the order of keyword arguments is maintained.
            # In earlier versions the order is not guaranteed; the default
            # value for the enum instantiation can then be any of the defined values
            self.assertEqual(self.FileKind(), 0)
        else:
            self.assertIn(self.FileKind(), (0, 1, 2))
    
    def test_enum_does_not_accept_invalid_value(self):
        self.assertRaises(ValueError, self.MyEnum, 0)
        self.assertRaises(ValueError, self.FileKind, -1)
    
    def test_enum_class_can_be_instantiated_with_named_values(self):
        v = self.MyEnum(BLUE) # @UndefinedVariable
        self.assertEqual(v, 5)
        v = self.FileKind(EXEC) # @UndefinedVariable
        self.assertEqual(v, 2)

    def test_existing_enumerations_cannot_be_extended(self):
        self.assertRaises(ValueError, self.MyEnum.typedef, GREEN=8)

    def test_existing_enumerations_can_be_aliased(self):
        alias = self.MyEnum.typedef()
        self.assertIs(alias.RED, self.MyEnum.RED)

        
class TestBoolean(unittest.TestCase):
    def test_boolean_values(self):
        self.assertEqual(xdr.FALSE, 0) # @UndefinedVariable
        self.assertEqual(xdr.TRUE, 1) # @UndefinedVariable
        self.assertIsInstance(xdr.FALSE, xdr.Boolean) # @UndefinedVariable
        self.assertIsInstance(xdr.TRUE, xdr.Enumeration) # @UndefinedVariable
        self.assertIs(xdr.FALSE.__class__, xdr.Boolean) # @UndefinedVariable


class TestFloats(unittest.TestCase):
    def test_default_instantation(self):
        for float_type in (xdr.Float32, xdr.Float64, xdr.Float128):
            with self.subTest(float_type=float_type):
                self.assertEqual(float_type(), 0.0)

    def test_standard_instantiation(self):
        for float_type in (xdr.Float32, xdr.Float64, xdr.Float128):
            with self.subTest(float_type=float_type):
                self.assertEqual(float_type(-0.375), -0.375)
    
    def test_nan_and_inf(self):
        for float_type in (xdr.Float32, xdr.Float64, xdr.Float128):
            with self.subTest(float_type=float_type):
                self.assertTrue(math.isnan(float_type('nan')))
                self.assertTrue(math.isnan(float_type('-nan')))
                self.assertTrue(math.isinf(float_type('inf')))
                self.assertTrue(math.isinf(float_type('-inf')))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()