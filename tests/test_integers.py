'''
Created on 28 dec. 2015

@author: Ruud
'''
import unittest

from xdrlib2 import *
from xdrlib2.xdr_types import _padding

class TestIntegers(unittest.TestCase):
    def test_default_instantion(self):
        self.assertEqual(Int32(), 0)
        self.assertEqual(Int32u(), 0)
        self.assertEqual(Int64(), 0)
        self.assertEqual(Int64u(), 0)       
    
    def test_integers_with_invalid_values(self):
        for v in (-2**31-1, 2**31):
            self.assertRaises(ValueError, Int32, v)
        for v in (-1, 2**32):
            self.assertRaises(ValueError, Int32u, v)
        for v in (-2**63-1, 2**63):
            self.assertRaises(ValueError, Int64, v)
        for v in (-1, 2**64):
            self.assertRaises(ValueError, Int64u, v)
    
    def test_binary_representation(self):
        for v, p32, p64 in ((0, (0 .to_bytes(4, byteorder) + _padding(4)), (0 .to_bytes(8, byteorder) + _padding(8))),
                            (8, (8 .to_bytes(4, byteorder) + _padding(4)), (8 .to_bytes(8, byteorder) + _padding(8))),
                            (256, (256 .to_bytes(4, byteorder) + _padding(4)), (256 .to_bytes(8, byteorder) + _padding(8)))):
            self.assertEqual(encode(Int32(v)), p32)
            self.assertEqual(encode(Int32u(v)), p32)
            self.assertEqual(encode(Int64(v)), p64)
            self.assertEqual(encode(Int64u(v)), p64)
        
        for v, p in ((-2**31, b'\x80\0\0\0' + _padding(4)),
                     (2**31-1, b'\x7f\xff\xff\xff' + _padding(4))):
            self.assertEqual(encode(Int32(v)), p)
        
        for v, p in ((2**31, b'\x80\0\0\0' + _padding(4)),
                     (2**32-1, b'\xff\xff\xff\xff' + _padding(4))):
            self.assertEqual(encode(Int32u(v)), p)
        
        for v, p in ((-2**63, b'\x80\0\0\0\0\0\0\0' + _padding(8)),
                     (2**63-1, b'\x7f\xff\xff\xff\xff\xff\xff\xff' + _padding(8))):
            self.assertEqual(encode(Int64(v)), p)
        
        for v, p in ((2**63, b'\x80\0\0\0\0\0\0\0' + _padding(8)),
                     (2**64-1, b'\xff\xff\xff\xff\xff\xff\xff\xff' + _padding(8))):
            self.assertEqual(encode(Int64u(v)), p)
    
    def test_decoding(self):
        for v, p32, p64 in ((0, (b'\0\0\0\0' + _padding(4)), (b'\0\0\0\0\0\0\0\0' + _padding(8))),
                            (8, 8 .to_bytes(4, byteorder) + _padding(4), 8 .to_bytes(8, byteorder) + _padding(8)),
                            (256, 256 .to_bytes(4, byteorder) + _padding(4), 256 .to_bytes(8, byteorder) + _padding(8)),
                            ):
            x = decode(Int32, p32)
            self.assertIsInstance(x, Int32)
            self.assertEqual(x, v)
            x = decode(Int32u, p32)
            self.assertIsInstance(x, Int32u)
            self.assertEqual(x, v)
            x = decode(Int64, p64)
            self.assertIsInstance(x, Int64)
            self.assertEqual(x, v)
            x = decode(Int64u, p64)
            self.assertIsInstance(x, Int64u)
            self.assertEqual(x, v)

    def test_optional_integers(self):
        OptInt = Optional(Int32)
        absent = OptInt()
        self.assertIsInstance(absent, Void)
        self.assertEqual(absent, None)
        self.assertEqual(encode(absent), b'\0\0\0\0' + _padding(4))
        parsed = decode(OptInt, b'\0\0\0\0' + _padding(4))
        self.assertEqual(parsed, absent)
        self.assertIsInstance(parsed, Void)
        self.assertEqual(parsed, None)
        self.assertEqual(encode(parsed), b'\0\0\0\0' + _padding(4))
        
        present = OptInt(10)
        self.assertIsInstance(present, Int32)
        self.assertEqual(present, 10)
        self.assertEqual(encode(present), encode(TRUE) + 10 .to_bytes(4, byteorder) + _padding(4)) # @UndefinedVariable
        parsed = decode(OptInt, encode(TRUE) + 10 .to_bytes(4, byteorder) + _padding(4)) # @UndefinedVariable
        self.assertEqual(parsed, present)
        self.assertIsInstance(parsed, OptInt)
        self.assertEqual(encode(parsed), encode(TRUE) + 10 .to_bytes(4, byteorder) + _padding(4)) # @UndefinedVariable
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
