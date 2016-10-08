'''
Created on 8 okt. 2016

@author: Ruud
'''
import unittest

import xdrlib2 as xdr
from xdrlib2.xdr_types import _pad as pad

class TestIntegers(unittest.TestCase):

    def test_integer_type_accepts_values_in_range(self):
        value_set = {xdr.Int32: (-2**31, -1024, 0, 123456, 2**31-1),
                     xdr.Int32u: (0, 123456, 2**31, 2**32-1),
                     xdr.Int64: (-2**63, -2**33, 0, 123456, 2**31, 2**63-1),
                     xdr.Int64u: (0, 123456, 2**32, 2**63, 2**64-1)}
        
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            for value in value_set[integer_type]:
                with self.subTest(value=value):
                    self.assertEqual(integer_type(value), value)
    
    def test_integer_type_does_not_accept_values_out_of_range(self):
        value_set = {xdr.Int32: (-2**31-1, 2**31),
                     xdr.Int32u: (-1, 2**32),
                     xdr.Int64: (-2**63-1, 2**63),
                     xdr.Int64u: (-1, 2**64)}
        
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            for value in value_set[integer_type]:
                with self.subTest(value=value):
                    self.assertRaises(ValueError, integer_type, value)
    
    def test_integer_type_can_be_instantiated_with_string(self):
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            for args, value in ((("16", 10), 16),
                                (("32",), 32),
                                (("abcd", 16), 0xabcd),
                                (("765", 8), 0o765)):
                with self.subTest(args=args, value=value):
                    self.assertEqual(integer_type(*args), value)
    
    def test_optional_integer_type_present(self):
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            optional_integer_type = xdr.Optional(integer_type)
            
            x = optional_integer_type(1024)
            self.assertEqual(x, 1024)
            self.assertIsInstance(x, optional_integer_type)
            self.assertIsInstance(x, xdr.Optional)
            self.assertIsInstance(x, integer_type)
            self.assertIsInstance(x, int)
            self.assertFalse(isinstance(x, xdr.Void))
        
    def test_optional_integer_type_absent(self):
        for integer_type in (xdr.Int32, xdr.Int32u, xdr.Int64, xdr.Int64u):
            optional_integer_type = xdr.Optional(integer_type)
            
            y = optional_integer_type(None)
            self.assertEqual(y, None)
            self.assertIsInstance(y, optional_integer_type)
            self.assertIsInstance(y, xdr.Optional)
            self.assertIsInstance(y, xdr.Void)
            self.assertFalse(isinstance(y, integer_type))
            self.assertFalse(isinstance(y, int))
    
    def test_integer_encoding_and_decoding(self):
        encodings = {xdr.Int32: {-2**31: b'\x80\0\0\0',
                                 -1024: b'\xff\xff\xfc\x00',
                                 0: b'\0\0\0\0',
                                 123456: b'\0\x01\xe2\x40',
                                 2**31-1: b'\x7f\xff\xff\xff',
                                 },
                     xdr.Int32u: {0: b'\0\0\0\0',
                                  123456: b'\0\x01\xe2\x40',
                                  2**31-1: b'\x7f\xff\xff\xff',
                                  2**31: b'\x80\0\0\0',
                                  2**32-1: b'\xff\xff\xff\xff',
                                  },
                     xdr.Int64: {-2**63: b'\x80\0\0\0\0\0\0\0',
                                 -2**33: b'\xff\xff\xff\xfe\x00\x00\x00\x00',
                                 0: b'\0\0\0\0\0\0\0\0',
                                 123456: b'\0\0\0\0\0\x01\xe2\x40',
                                 2**31: b'\0\0\0\0\x80\0\0\0',
                                 2**63-1: b'\x7f\xff\xff\xff\xff\xff\xff\xff',
                                 },
                     xdr.Int64u: {0: b'\0\0\0\0\0\0\0\0',
                                  123456: b'\0\0\0\0\0\x01\xe2\x40',
                                  2**32: b'\0\0\0\x01\0\0\0\0',
                                  2**63: b'\x80\0\0\0\0\0\0\0',
                                  2**64-1: b'\xff\xff\xff\xff\xff\xff\xff\xff',
                                  },
                     }
        for integer_type, value_set in encodings.items():
            for integer_value, encoded_value in value_set.items():
                with self.subTest(integer_type=integer_type, integer_value=integer_value, encoded_value=encoded_value):
                    encoded_value = pad(encoded_value)
                    x = integer_type(integer_value)
                    self.assertEqual(x.to_bytes(), encoded_value)
                    y = integer_type.from_bytes(encoded_value)
                    self.assertEqual(y, integer_value)
                    self.assertEqual(y, x)
                    self.assertEqual(type(y), integer_type)
                     
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()