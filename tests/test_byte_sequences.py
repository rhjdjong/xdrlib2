'''
Created on 29 dec. 2015

@author: Ruud
'''
import unittest

from xdrlib2 import *
from xdrlib2.xdr_types import _padding

class TestFixedOpaque(unittest.TestCase):
    class FixedLengthOpaque(FixedOpaque):
        size = 5
    
    def test_fixed_length_opaque_from_bytes(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(byte_str)
        self.assertIsInstance(blob, FixedOpaque)
        self.assertIsInstance(blob, bytearray)
        self.assertEqual(blob, byte_str)
    
    def test_fixed_length_opaque_from_integers(self):
        int_list = [0, 255,0xab, 0xcd, 1]
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(int_list)
        self.assertIsInstance(blob, FixedOpaque)
        self.assertIsInstance(blob, bytearray)
        self.assertEqual(blob, byte_str)
        
    def test_encoding_and_decoding(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(byte_str)
        bp = encode(blob)
        self.assertEqual(bp, byte_str + _padding(5))
        x = decode(self.FixedLengthOpaque, bp)
        self.assertIsInstance(x, self.FixedLengthOpaque)
        self.assertEqual(x, blob)

    def test_fixed_length_opaque_default_value(self):
        x = self.FixedLengthOpaque()
        self.assertEqual(x, b'\0\0\0\0\0')

    def test_fixed_length_opaque_requries_correctly_sized_arguments(self):
        self.assertRaises(ValueError, self.FixedLengthOpaque, b'123')
        self.assertRaises(ValueError, self.FixedLengthOpaque, b'1234567890')
    
    def test_fixed_length_opaque_decode_errors(self):
        self.assertRaises(ValueError, decode, self.FixedLengthOpaque, b'1234' + _padding(4))
        self.assertRaises(ValueError, decode, self.FixedLengthOpaque, b'12345678' + _padding(8))
    
    def test_fixed_opaque_class_construction(self):
        my_cls = FixedOpaque(size=5)
        self.assertTrue(issubclass(my_cls, FixedOpaque))
        self.assertTrue(FixedOpaque in my_cls.__mro__)
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = my_cls(byte_str)
        self.assertIsInstance(blob, bytearray)
        self.assertIsInstance(blob, my_cls)
        self.assertEqual(blob, byte_str)
        bp = encode(blob)
        self.assertEqual(bp, byte_str + _padding(5))
        self.assertEqual(decode(my_cls, bp), blob)
    
    def test_fixed_opaque_with_size_0(self):
        my_cls = FixedOpaque(size=0)
        blob = my_cls(())
        self.assertIsInstance(blob, bytearray)
        self.assertIsInstance(blob, my_cls)
        self.assertEqual(blob, b'')
        bp = encode(blob)
        self.assertEqual(bp, b'')
        self.assertEqual(decode(my_cls, bp), blob)

    def test_fixed_length_opaque_item_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(byte_str)
        blob[2] = 0
        self.assertEqual(blob, b'\0\xff\0\xcd\x01')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\xff\0\xcd\x01' + _padding(5))
        self.assertEqual(decode(self.FixedLengthOpaque, bp), blob)

    def test_fixed_length_opaque_slice_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(byte_str)
        blob[2:4] = b'\0\0'
        self.assertEqual(blob, b'\0\xff\0\0\x01')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\xff\0\0\x01' + _padding(5))
        self.assertEqual(decode(self.FixedLengthOpaque, bp), blob)

    def test_fixed_length_size_change_fails(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(byte_str)
        with self.assertRaises(ValueError):
            del blob[2]
        with self.assertRaises(ValueError):
            blob[2:4] = b'\0'
        self.assertRaises(ValueError, blob.append, 3)
        self.assertRaises(ValueError, blob.extend, b'no')
        with self.assertRaises(ValueError):
            blob += b'no way'
    
    def test_optional_fixed_length(self):
        optType = Optional(self.FixedLengthOpaque)
        byte_str = b'\0\xff\xab\xcd\x01'
        yes = optType(byte_str)
        no = optType()
        self.assertIsInstance(yes, self.FixedLengthOpaque)
        self.assertEqual(yes, byte_str)
        self.assertEqual(no, None)
        y_b = encode(yes)
        n_b = encode(no)
        self.assertEqual(y_b, encode(TRUE) + byte_str + _padding(5)) # @UndefinedVariable
        self.assertEqual(n_b, encode(FALSE)) # @UndefinedVariable
        self.assertEqual(decode(optType, y_b), yes)
        self.assertEqual(decode(optType, n_b), no)
        
    def test_explicit_subclassing(self):
        subcls = FixedOpaque.typedef(size=5)
        x = subcls(b'12345')
        self.assertIsInstance(x, FixedOpaque)
        self.assertEqual(encode(x), b'12345' + _padding(5))
        

class TestVarOpaque(unittest.TestCase):
    class VarLengthOpaque(VarOpaque):
        _size = 9
 
    def test_var_length_opaque_from_bytes(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        self.assertIsInstance(blob, bytearray)
        self.assertIsInstance(blob, self.VarLengthOpaque)
        self.assertEqual(blob, byte_str)
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(5)) + byte_str + _padding(5))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
         
    def test_var_length_opaque_from_integers(self):
        int_list = [0, 255,0xab, 0xcd, 1]
        byte_str = bytes(int_list)
        blob = self.VarLengthOpaque(byte_str)
        self.assertIsInstance(blob, bytearray)
        self.assertIsInstance(blob, self.VarLengthOpaque)
        self.assertEqual(blob, byte_str)
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(5)) + byte_str + _padding(5))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
         
    def test_var_length_opaque_one_by_one_from_integers(self):
        int_list = [0, 255,0xab, 0xcd, 1]
        byte_str = bytes(int_list)
        blob = self.VarLengthOpaque(())
        self.assertIsInstance(blob, bytearray)
        self.assertIsInstance(blob, self.VarLengthOpaque)
        identity = id(blob)
        self.assertEqual(blob, b'')
        for i, v in enumerate(int_list):
            blob.append(v)
            self.assertEqual(blob, byte_str[:i+1])
            self.assertEqual(identity, id(blob))
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(5)) + byte_str + _padding(5))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
         
    def test_var_length_opaque_errors(self):
        self.assertRaises(ValueError, self.VarLengthOpaque, b'1234567890')
     
    def test_var_length_opaque_decode_errors(self):
        self.assertRaises(ValueError, decode, self.VarLengthOpaque, encode(Int32u(5)) + b'1234')
        self.assertRaises(ValueError, decode, self.VarLengthOpaque, encode(Int32u(10)) + b'1234567890' + _padding(9))
        self.assertRaises(ValueError, decode, self.VarLengthOpaque, encode(Int32u(1)) + b'abcd' + _padding(4))
     
    def test_can_append_to_var_length_opaque(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        for b in b'fill':
            blob.append(b)
        self.assertEqual(blob, byte_str + b'fill')
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(9)) + byte_str + b'fill' + _padding(9))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
 
    def test_can_extend_var_length_opaque(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        blob.extend(b'fill')
        self.assertEqual(blob, byte_str + b'fill')
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(9)) + byte_str + b'fill' + _padding(9))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
     
    def test_can_delete_item_from_var_length_opaque(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        del blob[3]
        self.assertEqual(blob, b'\0\xff\xab\x01')
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(4)) + b'\0\xff\xab\x01' + _padding(4))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
         
    def test_can_delete_slice_from_var_length_opaque(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        del blob[1:3]
        self.assertEqual(blob, b'\0\xcd\x01')
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(3)) + b'\0\xcd\x01' + _padding(3))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
     
    def test_error_when_var_length_opaque_grows_too_large(self):
        byte_str = bytes(b'abcdefgh')
        blob = self.VarLengthOpaque(byte_str)
        blob.extend(b'i')
        self.assertEqual(blob, b'abcdefghi')
        self.assertRaises(ValueError, blob.extend, b'j')
        self.assertRaises(ValueError, blob.append, 10)
        with self.assertRaises(ValueError):
            blob[0:0] = b'way too long'
        with self.assertRaises(ValueError):
            blob[-1:] = [0, 1, 2]
        with self.assertRaises(ValueError):
            blob += b'jkl'
        with self.assertRaises(ValueError):
            blob *= 5
     
    def test_var_opaque_class_construction(self):
        my_cls = VarOpaque(size=9)
        self.assertTrue(issubclass(my_cls, VarOpaque))
        self.assertTrue(VarOpaque in my_cls.__mro__)
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = my_cls(byte_str)
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(5)) + byte_str + _padding(5))
        self.assertEqual(decode(my_cls, bp), blob)
     
    def test_empty_var_opaque(self):
        blob = self.VarLengthOpaque(b'')
        bp = encode(blob)
        self.assertEqual(blob, b'')
        self.assertEqual(bp, encode(Int32u(0)))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
 
    def test_var_length_opaque_item_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        blob[2] = 0
        self.assertEqual(blob, b'\0\xff\0\xcd\x01')
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(5)) + b'\0\xff\0\xcd\x01' + _padding(5))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
     
    def test_var_length_opaque_augmented_addition(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        blob += b'fill'
        self.assertEqual(blob, byte_str + b'fill')
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(9)) + byte_str + b'fill' + _padding(9))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
 
    def test_var_length_opaque_slice_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        blob[2:4] = b'\0\0\xff\xff'
        self.assertEqual(blob, b'\0\xff\0\0\xff\xff\x01')
        bp = encode(blob)
        self.assertEqual(bp, encode(Int32u(7)) + b'\0\xff\0\0\xff\xff\x01' + _padding(7))
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
     
    def test_optional_var_length_opaque(self):
        optType = Optional(self.VarLengthOpaque)
        byte_str = b'\0\xff\xab\xcd\x01'
        yes = optType(byte_str)
        no = optType()
        self.assertIsInstance(yes, self.VarLengthOpaque)
        self.assertEqual(yes, byte_str)
        self.assertEqual(no, None)
        y_b = encode(yes)
        n_b = encode(no)
        self.assertEqual(y_b, encode(TRUE) + encode(Int32u(5)) + byte_str + _padding(5)) # @UndefinedVariable
        self.assertEqual(n_b, encode(FALSE)) # @UndefinedVariable
        self.assertEqual(decode(optType, y_b), yes)
        self.assertEqual(decode(optType, n_b), no)
         
    def test_explicit_subclassing(self):
        subcls = VarOpaque.typedef(size=5)
        x = subcls(b'123')
        self.assertIsInstance(x, VarOpaque)
        self.assertEqual(encode(x), encode(Int32u(3)) +  b'123' + _padding(3))

 
class TestString(unittest.TestCase):
    class MyString(String):
        _size = 15
     
    def test_string_packing(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        self.assertIsInstance(s, bytearray)
        self.assertIsInstance(s, self.MyString)
        self.assertEqual(s, byte_str)
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(12)) + byte_str + _padding(12))
        self.assertEqual(decode(self.MyString, bp), s)
     
    def test_string_errors(self):
        self.assertRaises(ValueError, self.MyString, b'This is way too long')
     
    def test_string_unpack_errors(self):
        self.assertRaises(ValueError, decode, self.MyString, b'\0\0\0\x0ftoo short')
        self.assertRaises(ValueError, decode, self.MyString, b'\0\0\0\x0fthis is way too long' + _padding(20))
 
    def test_string_class_construction(self):
        my_cls = String(size=15)
        self.assertTrue(issubclass(my_cls, String))
        self.assertTrue(String in my_cls.__mro__)
        byte_str = b'Hello world!'
        s = my_cls(byte_str)
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(12)) + byte_str)
        self.assertEqual(decode(my_cls, bp), s)
     
    def test_empty_string(self):
        s = self.MyString(b'')
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(0)))
        self.assertEqual(decode(self.MyString, bp), s)
      
    def test_can_append_to_string(self):
        byte_str = b'Hello '
        s = self.MyString(byte_str)
        for b in b'world!':
            s.append(b)
        self.assertEqual(s, byte_str + b'world!')
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(12)) + b'Hello world!' + _padding(12))
        self.assertEqual(decode(self.MyString, bp), s)
 
    def test_can_extend_string(self):
        byte_str = b'Hello '
        s = self.MyString(byte_str)
        s.extend(b'world!')
        self.assertEqual(s, b'Hello world!')
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(12)) + b'Hello world!' + _padding(12))
        self.assertEqual(decode(self.MyString, bp), s)
     
    def test_can_delete_item_from_string(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        del s[4]
        self.assertEqual(s, b'Hell world!')
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(11)) + b'Hell world!' + _padding(11))
        self.assertEqual(decode(self.MyString, bp), s)
         
    def test_can_delete_slice_from_string(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        del s[1:4]
        self.assertEqual(s, b'Ho world!')
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(9)) + b'Ho world!' + _padding(9))
        self.assertEqual(decode(self.MyString, bp), s)
 
    def test_string_grows_too_large(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        self.assertRaises(ValueError, s.extend, b'How are you?')
        with self.assertRaises(ValueError):
            for c in b'How are you':
                s.append(c)
        with self.assertRaises(ValueError):
            s[0:0] = b'This prefix is way too long'
        with self.assertRaises(ValueError):
            s[-1:] = b'This tail is way to long'
        with self.assertRaises(ValueError):
            s += b'How are you?'
     
    def test_string_item_replacement(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        s[6] = ord(b'W')
        self.assertEqual(s, b'Hello World!')
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(12)) + b'Hello World!' + _padding(12))
        self.assertEqual(decode(self.MyString, bp), s)
     
    def test_string_augmented_addition(self):
        byte_str = b'Hello '
        s = self.MyString(byte_str)
        s += b'world!'
        self.assertEqual(s, b'Hello world!')
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(12)) + b'Hello world!' + _padding(12))
        self.assertEqual(decode(self.MyString, bp), s)
 
    def test_string_slice_replacement(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        s[1:5] = b'i there'
        self.assertEqual(s, b'Hi there world!')
        bp = encode(s)
        self.assertEqual(bp, encode(Int32u(15)) + b'Hi there world!' + _padding(15))
        self.assertEqual(decode(self.MyString, bp), s)
     
    def test_optional_string(self):
        optType = Optional(self.MyString)
        byte_str = b'Hello world!'
        yes = optType(byte_str)
        no = optType()
        self.assertIsInstance(yes, self.MyString)
        self.assertEqual(yes, byte_str)
        self.assertEqual(no, None)
        y_b = encode(yes)
        n_b = encode(no)
        self.assertEqual(y_b, encode(TRUE) + encode(Int32u(12)) + byte_str + _padding(12))  # @UndefinedVariable
        self.assertEqual(n_b, encode(FALSE))  # @UndefinedVariable
        self.assertEqual(decode(optType, y_b), yes)
        self.assertEqual(decode(optType, n_b), no)

    def test_explicit_subclassing(self):
        subcls = String.typedef(size=5)
        x = subcls(b'123')
        self.assertIsInstance(x, String)
        self.assertEqual(encode(x), encode(Int32u(3)) + b'123' + _padding(3))
             

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()