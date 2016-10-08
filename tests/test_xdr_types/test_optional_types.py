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
        
    def test_instantiated_optional_integer_is_instance_of_integer(self):
        x = self.optional_integer_type(1024)
        self.assertIsInstance(x, xdr.Int32)
        self.assertIsInstance(x, self.optional_integer_type)
        self.assertIsInstance(x, xdr.Optional)
    
    def test_absent_optional_integer_is_instance_of_Void(self):
        x = self.optional_integer_type(None)
        self.assertNotIsInstance(x, xdr.Int32)
        self.assertIsInstance(x, xdr.Void)
        self.assertIsInstance(x, self.optional_integer_type)
        self.assertIsInstance(x, xdr.Optional)
    
    def test_present_optional_value_can_be_encoded_through_optional_class(self):
        encoded_value = self.optional_integer_type.to_bytes(self.optional_integer_type(3))
        self.assertEqual(encoded_value, b'\0\0\0\x01' b'\0\0\0\x03')
    
    def test_absent_optional_value_can_be_encoded_through_optional_class(self):
        encoded_value = self.optional_integer_type.to_bytes(self.optional_integer_type())
        self.assertEqual(encoded_value, b'\0\0\0\0')
    
    def test_present_optional_value_can_be_decoded_through_optional_class(self):
        x = self.optional_integer_type.from_bytes(b'\0\0\0\x01' b'\0\0\0\x03')
        self.assertEqual(x, 3)
        self.assertIsInstance(x, self.optional_integer_type)
        self.assertIsInstance(x, xdr.Int32)
        
    def test_absent_optional_value_can_be_decoded_through_optional_class(self):
        x = self.optional_integer_type.from_bytes(b'\0\0\0\0')
        self.assertEqual(x, None)
        self.assertIsInstance(x, self.optional_integer_type)
        self.assertIsInstance(x, xdr.Void)
    
    def test_present_optional_value_can_be_encoded_through_instance(self):
        x = self.optional_integer_type(3)
        self.assertEqual(x.to_bytes(), b'\0\0\0\x01' b'\0\0\0\x03')
    
    def test_absent_optional_value_can_be_encoded_through_instance(self):
        x = self.optional_integer_type()
        self.assertEqual(x.to_bytes(), b'\0\0\0\0')
    
    def test_optional_value_can_be_decoded_through_present_instance(self):
        x = self.optional_integer_type(2)
        y = x.from_bytes(b'\0\0\0\x01' b'\0\0\0\x03')
        self.assertEqual(y, 3)
        self.assertIsInstance(y, self.optional_integer_type)
        self.assertIsInstance(y, xdr.Int32)
        z = x.from_bytes(b'\0\0\0\0')
        self.assertEqual(z, None)
        self.assertIsInstance(z, self.optional_integer_type)
        self.assertIsInstance(z, xdr.Void)
    
    def test_optional_value_can_be_decoded_through_absent_instance(self):
        x = self.optional_integer_type()
        y = x.from_bytes(b'\0\0\0\x01' b'\0\0\0\x03')
        self.assertEqual(y, 3)
        self.assertIsInstance(y, self.optional_integer_type)
        self.assertIsInstance(y, xdr.Int32)
        z = x.from_bytes(b'\0\0\0\0')
        self.assertEqual(z, None)
        self.assertIsInstance(z, self.optional_integer_type)
        self.assertIsInstance(z, xdr.Void)
    
    def test_optional_decorator_is_idempotent(self):
        new_optional_type = xdr.Optional(self.optional_integer_type)
        self.assertIs(new_optional_type, self.optional_integer_type)
    
    def test_void_cannot_be_made_optional(self):
        with self.assertRaises(ValueError):
            _ = xdr.Optional(xdr.Void)
    
    def test_verify_class_hierarchy(self):
        x = self.optional_integer_type(3)
        y = self.optional_integer_type()
        self.assertTupleEqual(self.optional_integer_type.__bases__, (xdr.Optional,))
        self.assertTupleEqual(type(x).__bases__, (self.optional_integer_type, xdr.Int32))
        self.assertTupleEqual(type(y).__bases__, (self.optional_integer_type, xdr.Void))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()