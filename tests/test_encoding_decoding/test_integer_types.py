'''
Created on 11 okt. 2016

@author: Ruud
'''
import unittest
import math

import xdrlib2 as xdr
from xdrlib2.xdr_types import _pad as pad
from xdrlib2.xdr_types import _pad_size as pad_size
from xdrlib2.xdr_types import _padding as padding
from xdrlib2.xdr_base import byteorder

class TestIntegerEncodingDecoding(unittest.TestCase):
    
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
                with self.subTest(integer_type=integer_type, integer_value=integer_value):
                    encoded_value = pad(encoded_value)
                    x = integer_type(integer_value)
                    self.assertEqual(x.encode(), encoded_value)
                    y = integer_type.decode(encoded_value)
                    self.assertEqual(y, integer_value)
                    self.assertEqual(y, x)
                    self.assertEqual(type(y), integer_type)
                     
    def test_encoding_directly_via_type(self):
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
                with self.subTest(integer_type=integer_type, integer_value=integer_value):
                    encoded_value = pad(encoded_value)
                    self.assertEqual(integer_type.encode(integer_value), encoded_value)


class TestEnumeration(unittest.TestCase):
    class MyEnum(xdr.Enumeration):
        RED = 2
        YELLOW = 3
        BLUE = 5
    
    FileKind = xdr.Enumeration.typedef(TEXT=0, DATA=1, EXEC=2)

    def test_enum_encoding_and_decoding(self):
        for v, p in ((RED, xdr.Int32(2).encode()), # @UndefinedVariable
                     (YELLOW, xdr.Int32(3).encode()), # @UndefinedVariable
                     (BLUE, xdr.Int32(5).encode()), # @UndefinedVariable
                    ):
            self.assertEqual(v.encode(), p)
            x = self.MyEnum.decode(p)
            self.assertIsInstance(x, self.MyEnum)
            self.assertEqual(x, v)
        for v, p in ((TEXT, xdr.Int32(0).encode()), # @UndefinedVariable
                     (DATA, xdr.Int32(1).encode()), # @UndefinedVariable
                     (EXEC, xdr.Int32(2).encode()), # @UndefinedVariable
                    ):
            self.assertEqual(v.encode(), p)
            x = self.FileKind.decode(p)
            self.assertIsInstance(x, self.FileKind)
            self.assertEqual(x, v)
    
    def test_decoding_invalid_data_fails(self):
        with self.assertRaises(ValueError):
            _ = self.MyEnum.decode(xdr.Int32(0).encode())
        with self.assertRaises(ValueError):
            _ = self.FileKind.decode(xdr.Int32(0x07ffffff).encode())
    
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()