'''
Created on 8 okt. 2016

@author: Ruud
'''
import unittest

import xdrlib2 as xdr
    
class TestOptionalTypes(unittest.TestCase):
    def setUp(self):
        self.optional_integer_type = xdr.Optional(xdr.Int32)
    
    def test_optional_class_is_subclass_of_Optional(self):
        self.assertTrue(issubclass(self.optional_integer_type, xdr.Optional))
    
    def test_optional_class_name_is_derived_from_original_class(self):
        self.assertEqual(self.optional_integer_type.__name__, '*Int32')

    def test_optional_integer_is_not_a_subtype_of_integer(self):
        self.assertFalse(issubclass(self.optional_integer_type, xdr.Int32))
        
    def test_present_optional_value_instantiation(self):
        for cls in (self.optional_integer_type, # direct instantiation
                    self.optional_integer_type(3).__class__, # through the class of a present value
                    self.optional_integer_type(None).__class__): # through the class of an absent value
            with self.subTest(cls=cls):
                y = cls(5)
                self.assertEqual(y, 5)
                self.assertIsInstance(y, xdr.Int32)
                self.assertIsInstance(y, self.optional_integer_type)
                self.assertIsInstance(y, xdr.Optional)
        
    def test_absent_optional_value_instantiation(self):
        for cls in (self.optional_integer_type, # direct instantiation
                    self.optional_integer_type(3).__class__, # through the class of a present value
                    self.optional_integer_type(None).__class__): # through the class of an absent value
            with self.subTest(cls=cls):
                y = cls(None)
                self.assertEqual(y, None)
                self.assertNotIsInstance(y, xdr.Int32)
                self.assertIsInstance(y, xdr.Void)
                self.assertIsInstance(y, self.optional_integer_type)
                self.assertIsInstance(y, xdr.Optional)
        
    def test_optional_decorator_is_idempotent(self):
        new_optional_type = xdr.Optional(self.optional_integer_type)
        self.assertIs(new_optional_type, self.optional_integer_type)
    
    def test_void_cannot_be_made_optional(self):
        with self.assertRaises(TypeError):
            _ = xdr.Optional(xdr.Void)
    
    def test_cannot_create_optional_classes_through_derived_optional_class(self):
        self.assertRaises(TypeError, self.optional_integer_type, xdr.Float32)
    
    def test_verify_class_hierarchy(self):
        x = self.optional_integer_type(3)
        y = self.optional_integer_type()
        self.assertTupleEqual(self.optional_integer_type.__bases__, (xdr.Optional,))
        self.assertTupleEqual(type(x).__bases__, (self.optional_integer_type, xdr.Int32))
        self.assertTupleEqual(type(y).__bases__, (self.optional_integer_type, xdr.Void))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()