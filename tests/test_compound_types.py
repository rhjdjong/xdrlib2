'''
Created on 29 dec. 2015

@author: Ruud
'''
import unittest

import xdrlib2
from xdrlib2 import pack, unpack


class TestOpaque(unittest.TestCase):
    class FixedLengthOpaque(xdrlib2.FixedOpaque):
        _size = 5
    
    def test_fixed_length_opaque(self):
        blob = self.FixedLengthOpaque(b'\0\xff\xab\xcd\x01')
        bp = pack(blob)
        self.assertEqual(bp, b'\0\xff\xab\xcd\x01\0\0\0')
        self.assertEqual(unpack(self.FixedLengthOpaque, bp), blob)
    
    
    def test_fixed_length_opaque_errors(self):
        self.assertRaises(ValueError, self.FixedLengthOpaque, b'123')
        self.assertRaises(ValueError, self.FixedLengthOpaque, b'1234567890')
    
    def test_fixed_length_opaque_unpack_errors(self):
        self.assertRaises(ValueError, unpack, self.FixedLengthOpaque, b'123')
        self.assertRaises(ValueError, unpack, self.FixedLengthOpaque, b'1234567890')
    

class TestVarOpaque(unittest.TestCase):
    class VarLengthOpaque(xdrlib2.VarOpaque):
        _size = 9

    def test_var_length_opaque(self):
        blob = self.VarLengthOpaque(b'\0\xff\xab\xcd\x01')
        bp = pack(blob)
        self.assertEqual(bp, b'\0\0\0\x05\0\xff\xab\xcd\x01\0\0\0')
        self.assertEqual(unpack(self.VarLengthOpaque, bp), blob)
        
    def test_var_length_opaque_errors(self):
        self.assertRaises(ValueError, self.VarLengthOpaque, b'1234567890')
    
    def test_var_length_opaque_unpack_errors(self):
        self.assertRaises(ValueError, unpack, self.VarLengthOpaque, b'\0\0\0\x05123')
        self.assertRaises(ValueError, unpack, self.VarLengthOpaque, b'\0\0\0\x0a1234567890\0\0\0')
    

class TestString(unittest.TestCase):
    class MyString(xdrlib2.String):
        _size = 15
    
    def test_string_packing(self):
        s = self.MyString(b'Hello world!')
        bp = pack(s)
        self.assertEqual(bp, b'\0\0\0\x0cHello world!')
        self.assertEqual(unpack(self.MyString, bp), s)
    
    def test_string_errors(self):
        self.assertRaises(ValueError, self.MyString, b'This is way too long')
    
    def test_string_unpack_errors(self):
        self.assertRaises(ValueError, unpack, self.MyString, b'\0\0\0\x0ftoo short')
        self.assertRaises(ValueError, unpack, self.MyString, b'\0\0\0\x0fthis is way too long')


class TestFixedArray(unittest.TestCase):
    class IntArray(xdrlib2.FixedArray):
        _element_type = xdrlib2.Int32
        _size = 5
    
    class StringArray(xdrlib2.FixedArray):
        class MyString(xdrlib2.String):
            _size = 15
        
        _element_type = MyString
        _size = 5
        
    def test_fixed_array_packing(self):
        a = self.IntArray(range(5))
        bp = pack(a)
        self.assertEqual(bp, b'\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03\0\0\0\x04')
        self.assertEqual(unpack(self.IntArray, bp), a)
        
        b = self.StringArray((b'hello', b'this', b'is', b'the', b'message'))
        bp = pack(b)
        self.assertEqual(bp, b''.join((b'\0\0\0\x05hello\0\0\0',
                                       b'\0\0\0\x04this',
                                       b'\0\0\0\x02is\0\0',
                                       b'\0\0\0\x03the\0',
                                       b'\0\0\0\x07message\0')))
        self.assertEqual(unpack(self.StringArray, bp), b)
    
    def test_fixed_array_errors(self):
        self.assertRaises(ValueError, self.IntArray, [1, 2])
        self.assertRaises(ValueError, self.IntArray, range(10))
        self.assertRaises(ValueError, self.StringArray,
                          (b'a', b'b', b'c', b'd', b'this is way too long'))
    
    def test_fixed_array_unpack_errors(self):
        self.assertRaises(ValueError, unpack, self.IntArray,
                          b'\0\0\0\0')
        self.assertRaises(ValueError, unpack, self.IntArray,
                          b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0')
        self.assertRaises(ValueError, unpack, self.StringArray,
                          b''.join((b'\0\0\0\x05hello\0\0\0',
                                    b'\0\0\0\x04this',
                                    b'\0\0\0\x02is\0\0',
                                    b'\0\0\0\x03the\0',
                                    b'\0\0\0\x14message is too long.')))
        
        
class TestVarArray(unittest.TestCase):
    class IntArray(xdrlib2.VarArray):
        _element_type = xdrlib2.Int32
        _size = 5
    
    class StringArray(xdrlib2.VarArray):
        class MyString(xdrlib2.String):
            _size = 15
        
        _element_type = MyString
        _size = 7
        
    def test_var_array_packing(self):
        a = self.IntArray(range(4))
        bp = pack(a)
        self.assertEqual(bp, b'\0\0\0\x04\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03')
        self.assertEqual(unpack(self.IntArray, bp), a)
        
        b = self.StringArray((b'hello', b'this', b'is', b'the', b'message'))
        bp = pack(b)
        self.assertEqual(bp, b''.join((b'\0\0\0\x05',
                                       b'\0\0\0\x05hello\0\0\0',
                                       b'\0\0\0\x04this',
                                       b'\0\0\0\x02is\0\0',
                                       b'\0\0\0\x03the\0',
                                       b'\0\0\0\x07message\0')))
        self.assertEqual(unpack(self.StringArray, bp), b)
    
    def test_fixed_array_errors(self):
        self.assertRaises(ValueError, self.IntArray, range(10))
        self.assertRaises(ValueError, self.StringArray,
                          (b'a', b'b', b'c', b'd', b'this is way too long'))
    
    def test_fixed_array_unpack_errors(self):
        self.assertRaises(ValueError, unpack, self.IntArray,
                          b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0')
        self.assertRaises(ValueError, unpack, self.StringArray,
                          b''.join((b'\0\0\0\x05',
                                    b'\0\0\0\x05hello\0\0\0',
                                    b'\0\0\0\x04this',
                                    b'\0\0\0\x02is\0\0',
                                    b'\0\0\0\x03the\0',
                                    b'\0\0\0\x14message is too long.')))
        
        
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()