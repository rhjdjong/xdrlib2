'''
Created on 28 dec. 2015

@author: Ruud
'''
import unittest

from xdrlib2 import *

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
        for v, p32, p64 in ((0, b'\0\0\0\0', b'\0\0\0\0\0\0\0\0'),
                            (8, b'\0\0\0\x08', b'\0\0\0\0\0\0\0\x08'),
                            (256, b'\0\0\x01\0', b'\0\0\0\0\0\0\x01\0')
                            ):
            self.assertEqual(Int32(v).encode(), p32)
            self.assertEqual(Int32u(v).encode(), p32)
            self.assertEqual(Int64(v).encode(), p64)
            self.assertEqual(Int64u(v).encode(), p64)
        
        for v, p in ((-2**31, b'\x80\0\0\0'),
                     (2**31-1, b'\x7f\xff\xff\xff')):
            self.assertEqual(Int32(v).encode(), p)
        
        for v, p in ((2**31, b'\x80\0\0\0'),
                     (2**32-1, b'\xff\xff\xff\xff')):
            self.assertEqual(Int32u(v).encode(), p)
        
        for v, p in ((-2**63, b'\x80\0\0\0\0\0\0\0'),
                     (2**63-1, b'\x7f\xff\xff\xff\xff\xff\xff\xff')):
            self.assertEqual(Int64(v).encode(), p)
        
        for v, p in ((2**63, b'\x80\0\0\0\0\0\0\0'),
                     (2**64-1, b'\xff\xff\xff\xff\xff\xff\xff\xff')):
            self.assertEqual(Int64u(v).encode(), p)
    
    def test_decoding(self):
        for v, p32, p64 in ((0, b'\0\0\0\0', b'\0\0\0\0\0\0\0\0'),
                            (8, b'\0\0\0\x08', b'\0\0\0\0\0\0\0\x08'),
                            (256, b'\0\0\x01\0', b'\0\0\0\0\0\0\x01\0')
                            ):
            x = Int32.decode(p32)
            self.assertIsInstance(x, Int32)
            self.assertEqual(x, v)
            x = Int32u.decode(p32)
            self.assertIsInstance(x, Int32u)
            self.assertEqual(x, v)
            x = Int64.decode(p64)
            self.assertIsInstance(x, Int64)
            self.assertEqual(x, v)
            x = Int64u.decode(p64)
            self.assertIsInstance(x, Int64u)
            self.assertEqual(x, v)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
