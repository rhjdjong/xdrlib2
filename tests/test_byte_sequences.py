'''
Created on 29 dec. 2015

@author: Ruud
'''
import unittest

from xdrlib2 import *


class TestFixedBytes(unittest.TestCase):
    class FixedLengthOpaque(FixedBytes):
        size = 5
    
    def test_fixed_length_opaque_from_bytes(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(byte_str)
        self.assertIsInstance(blob, FixedBytes)
        self.assertIsInstance(blob, bytearray)
        self.assertEqual(blob, byte_str)
    
    def test_fixed_length_opaque_from_integers(self):
        int_list = [0, 255,0xab, 0xcd, 1]
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(int_list)
        self.assertIsInstance(blob, FixedBytes)
        self.assertIsInstance(blob, bytearray)
        self.assertEqual(blob, byte_str)
        
    def test_encoding_and_decoding(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(byte_str)
        bp = encode(blob)
        self.assertEqual(bp, byte_str + b'\0\0\0')
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
        self.assertRaises(ValueError, decode, self.FixedLengthOpaque, b'1234')
        self.assertRaises(ValueError, decode, self.FixedLengthOpaque, b'12345678')
    
    def test_fixed_opaque_class_construction(self):
        my_cls = FixedBytes.typedef('my_cls', 5)
        self.assertTrue(issubclass(my_cls, FixedBytes))
        self.assertTrue(FixedBytes in my_cls.__mro__)
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = my_cls(byte_str)
        self.assertIsInstance(blob, bytearray)
        self.assertIsInstance(blob, my_cls)
        self.assertEqual(blob, byte_str)
        bp = encode(blob)
        self.assertEqual(bp, byte_str + b'\0\0\0')
        self.assertEqual(decode(my_cls, bp), blob)
    
    def test_fixed_opaque_with_size_0(self):
        my_cls = FixedBytes.typedef('my_cls', 0)
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
        self.assertEqual(bp, b'\0\xff\0\xcd\x01' + b'\0\0\0')
        self.assertEqual(decode(self.FixedLengthOpaque, bp), blob)

    def test_fixed_length_opaque_slice_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.FixedLengthOpaque(byte_str)
        blob[2:4] = b'\0\0'
        self.assertEqual(blob, b'\0\xff\0\0\x01')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\xff\0\0\x01' + b'\0\0\0')
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
    
#     def test_optional_fixed_length_opaque(self):
#         optType = Optional(self.FixedLengthOpaque)
#         byte_str = b'\0\xff\xab\xcd\x01'
#         yes = optType(byte_str)
#         no = optType()
#         self.assertIsInstance(yes, self.FixedLengthOpaque)
#         self.assertEqual(yes, byte_str)
#         self.assertEqual(no, None)
#         y_b = pack(yes)
#         n_b = pack(no)
#         self.assertEqual(y_b, b'\0\0\0\x01' + byte_str + b'\0\0\0')
#         self.assertEqual(n_b, b'\0\0\0\0')
#         self.assertEqual(unpack(optType, y_b), yes)
#         self.assertEqual(unpack(optType, n_b), no)
        

class TestVarOpaque(unittest.TestCase):
    class VarLengthOpaque(VarBytes):
        _size = 9
 
    def test_var_length_opaque_from_bytes(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        self.assertIsInstance(blob, bytearray)
        self.assertIsInstance(blob, self.VarLengthOpaque)
        self.assertEqual(blob, byte_str)
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x05' + byte_str + b'\0\0\0')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
         
    def test_var_length_opaque_from_integers(self):
        int_list = [0, 255,0xab, 0xcd, 1]
        byte_str = bytes(int_list)
        blob = self.VarLengthOpaque(byte_str)
        self.assertIsInstance(blob, bytearray)
        self.assertIsInstance(blob, self.VarLengthOpaque)
        self.assertEqual(blob, byte_str)
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x05' + byte_str + b'\0\0\0')
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
        self.assertEqual(bp, b'\0\0\0\x05' + byte_str + b'\0\0\0')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
         
    def test_var_length_opaque_errors(self):
        self.assertRaises(ValueError, self.VarLengthOpaque, b'1234567890')
     
    def test_var_length_opaque_unpack_errors(self):
        self.assertRaises(ValueError, decode, self.VarLengthOpaque, b'\0\0\0\x051234')
        self.assertRaises(ValueError, decode, self.VarLengthOpaque, b'\0\0\0\x0a1234567890\0\0\0')
        self.assertRaises(ValueError, decode, self.VarLengthOpaque, b'\0\0\0\x01abcd')
     
    def test_can_append_to_var_length_opaque(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        for b in b'fill':
            blob.append(b)
        self.assertEqual(blob, byte_str + b'fill')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x09' + byte_str + b'fill' + b'\0\0\0')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
 
    def test_can_extend_var_length_opaque(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        blob.extend(b'fill')
        self.assertEqual(blob, byte_str + b'fill')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x09' + byte_str + b'fill' + b'\0\0\0')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
     
    def test_can_delete_item_from_var_length_opaque(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        del blob[3]
        self.assertEqual(blob, b'\0\xff\xab\x01')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x04\0\xff\xab\x01')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
         
    def test_can_delete_slice_from_var_length_opaque(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        del blob[1:3]
        self.assertEqual(blob, b'\0\xcd\x01')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x03\0\xcd\x01\0')
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
        my_cls = VarBytes.typedef('my_cls', 9)
        self.assertTrue(issubclass(my_cls, VarBytes))
        self.assertTrue(VarBytes in my_cls.__mro__)
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = my_cls(byte_str)
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x05' + byte_str + b'\0\0\0')
        self.assertEqual(decode(my_cls, bp), blob)
     
    def test_empty_var_opaque(self):
        blob = self.VarLengthOpaque(b'')
        bp = encode(blob)
        self.assertEqual(blob, b'')
        self.assertEqual(bp, b'\0\0\0\0')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
 
    def test_var_length_opaque_item_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        blob[2] = 0
        self.assertEqual(blob, b'\0\xff\0\xcd\x01')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x05\0\xff\0\xcd\x01' + b'\0\0\0')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
     
    def test_var_length_opaque_augmented_addition(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        blob += b'fill'
        self.assertEqual(blob, byte_str + b'fill')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x09' + byte_str + b'fill' + b'\0\0\0')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
 
    def test_var_length_opaque_slice_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        blob = self.VarLengthOpaque(byte_str)
        blob[2:4] = b'\0\0'
        self.assertEqual(blob, b'\0\xff\0\0\x01')
        bp = encode(blob)
        self.assertEqual(bp, b'\0\0\0\x05\0\xff\0\0\x01' + b'\0\0\0')
        self.assertEqual(decode(self.VarLengthOpaque, bp), blob)
     
#     def test_optional_var_length_opaque(self):
#         optType = Optional(self.VarLengthOpaque)
#         byte_str = b'\0\xff\xab\xcd\x01'
#         yes = optType(byte_str)
#         no = optType()
#         self.assertIsInstance(yes, self.VarLengthOpaque)
#         self.assertEqual(yes, byte_str)
#         self.assertEqual(no, None)
#         y_b = pack(yes)
#         n_b = pack(no)
#         self.assertEqual(y_b, b'\0\0\0\x01' + b'\0\0\0\x05' + byte_str + b'\0\0\0')
#         self.assertEqual(n_b, b'\0\0\0\0')
#         self.assertEqual(unpack(optType, y_b), yes)
#         self.assertEqual(unpack(optType, n_b), no)
#         
# 
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
        self.assertEqual(bp, b'\0\0\0\x0c' + byte_str)
        self.assertEqual(decode(self.MyString, bp), s)
     
    def test_string_errors(self):
        self.assertRaises(ValueError, self.MyString, b'This is way too long')
     
    def test_string_unpack_errors(self):
        self.assertRaises(ValueError, decode, self.MyString, b'\0\0\0\x0ftoo short')
        self.assertRaises(ValueError, decode, self.MyString, b'\0\0\0\x0fthis is way too long')
 
    def test_string_class_construction(self):
        my_cls = String.typedef('my_cls', 15)
        self.assertTrue(issubclass(my_cls, String))
        self.assertTrue(String in my_cls.__mro__)
        byte_str = b'Hello world!'
        s = my_cls(byte_str)
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x0c' + byte_str)
        self.assertEqual(decode(my_cls, bp), s)
     
    def test_empty_string(self):
        s = self.MyString(b'')
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\0')
        self.assertEqual(decode(self.MyString, bp), s)
      
    def test_can_append_to_string(self):
        byte_str = b'Hello '
        s = self.MyString(byte_str)
        for b in b'world!':
            s.append(b)
        self.assertEqual(s, byte_str + b'world!')
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x0c' + b'Hello world!')
        self.assertEqual(decode(self.MyString, bp), s)
 
    def test_can_extend_string(self):
        byte_str = b'Hello '
        s = self.MyString(byte_str)
        s.extend(b'world!')
        self.assertEqual(s, b'Hello world!')
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x0c' + b'Hello world!')
        self.assertEqual(decode(self.MyString, bp), s)
     
    def test_can_delete_item_from_string(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        del s[4]
        self.assertEqual(s, b'Hell world!')
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x0b' + b'Hell world!' + b'\0')
        self.assertEqual(decode(self.MyString, bp), s)
         
    def test_can_delete_slice_from_string(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        del s[1:4]
        self.assertEqual(s, b'Ho world!')
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x09' + b'Ho world!' + b'\0\0\0')
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
        self.assertEqual(bp, b'\0\0\0\x0c' + b'Hello World!')
        self.assertEqual(decode(self.MyString, bp), s)
     
    def test_string_augmented_addition(self):
        byte_str = b'Hello '
        s = self.MyString(byte_str)
        s += b'world!'
        self.assertEqual(s, b'Hello world!')
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x0c' + b'Hello world!')
        self.assertEqual(decode(self.MyString, bp), s)
 
    def test_string_slice_replacement(self):
        byte_str = b'Hello world!'
        s = self.MyString(byte_str)
        s[1:5] = b'i there'
        self.assertEqual(s, b'Hi there world!')
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x0f' + b'Hi there world!' + b'\0')
        self.assertEqual(decode(self.MyString, bp), s)
#     
#     def test_optional_string(self):
#         optType = Optional(self.MyString)
#         byte_str = b'Hello world!'
#         yes = optType(byte_str)
#         no = optType()
#         self.assertIsInstance(yes, self.MyString)
#         self.assertEqual(yes, byte_str)
#         self.assertEqual(no, None)
#         y_b = pack(yes)
#         n_b = pack(no)
#         self.assertEqual(y_b, b'\0\0\0\x01' + b'\0\0\0\x0c' + byte_str)
#         self.assertEqual(n_b, b'\0\0\0\0')
#         self.assertEqual(unpack(optType, y_b), yes)
#         self.assertEqual(unpack(optType, n_b), no)
#         
# 
# class TestFixedArray(unittest.TestCase):
#     class IntArray(FixedArray):
#         _element_type = Int32
#         _size = 5
#     
#     class StringArray(FixedArray):
#         class MyString(String):
#             _size = 15
#         
#         _element_type = MyString
#         _size = 5
#         
#     def test_fixed_array_packing(self):
#         a = self.IntArray(range(5))
#         self.assertIsInstance(a, list)
#         self.assertEqual(a, [0, 1, 2, 3, 4])
#         bp = pack(a)
#         self.assertEqual(bp, b'\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03\0\0\0\x04')
#         self.assertEqual(unpack(self.IntArray, bp), a)
#         
#         b = self.StringArray((b'hello', b'this', b'is', b'the', b'message'))
#         self.assertIsInstance(b, list)
#         self.assertEqual(b, [b'hello', b'this', b'is', b'the', b'message'])
#         bp = pack(b)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x05hello\0\0\0',
#                                        b'\0\0\0\x04this',
#                                        b'\0\0\0\x02is\0\0',
#                                        b'\0\0\0\x03the\0',
#                                        b'\0\0\0\x07message\0')))
#         self.assertEqual(unpack(self.StringArray, bp), b)
#     
#     def test_fixed_array_errors(self):
#         self.assertRaises(ValueError, self.IntArray, [1, 2])
#         self.assertRaises(ValueError, self.IntArray, range(10))
#         self.assertRaises(ValueError, self.StringArray,
#                           (b'a', b'b', b'c', b'd', b'this is way too long'))
#         a = self.IntArray(range(5))
#         with self.assertRaises(ValueError):
#             a.append(6)
#         with self.assertRaises(ValueError):
#             del a[0]
#     
#     def test_fixed_array_unpack_errors(self):
#         self.assertRaises(ValueError, unpack, self.IntArray,
#                           b'\0\0\0\0')
#         self.assertRaises(ValueError, unpack, self.IntArray,
#                           b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0')
#         self.assertRaises(ValueError, unpack, self.StringArray,
#                           b''.join((b'\0\0\0\x05hello\0\0\0',
#                                     b'\0\0\0\x04this',
#                                     b'\0\0\0\x02is\0\0',
#                                     b'\0\0\0\x03the\0',
#                                     b'\0\0\0\x14message is too long.')))
# 
#     def test_fixed_array_class_construction(self):
#         my_cls = FixedArrayType('my_cls', size=5, element_type=Int32)
#         self.assertTrue(issubclass(my_cls, FixedArray))
#         self.assertTrue(FixedArray in my_cls.__mro__)
#         a = my_cls(range(5))
#         bp = pack(a)
#         self.assertEqual(bp, b'\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03\0\0\0\x04')
#         self.assertEqual(unpack(my_cls, bp), a)
#     
#     def test_fixed_array_size_0(self):
#         my_cls = FixedArrayType('my_cls', size=0, element_type=Boolean)
#         a = my_cls(())
#         self.assertIsInstance(a, list)
#         self.assertEqual(a, [])
#         bp = pack(a)
#         self.assertEqual(bp, b'')
#         self.assertEqual(unpack(my_cls, bp), a)
#      
#     def test_fixed_array_item_replacement(self):
#         a = self.IntArray(range(5))
#         a[2] = 255
#         self.assertEqual(a, [0, 1, 255, 3, 4])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\xff',
#                                        b'\0\0\0\x03',
#                                        b'\0\0\0\x04')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
# 
#     def test_fixed_array_slice_replacement(self):
#         a = self.IntArray(range(5))
#         a[2:4] = [255, 256]
#         self.assertEqual(a, [0, 1, 255, 256, 4])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\xff',
#                                        b'\0\0\x01\0',
#                                        b'\0\0\0\x04')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
# 
#     def test_fixed_array_size_change_fails(self):
#         a = self.IntArray(range(5))
#         with self.assertRaises(ValueError):
#             del a[2]
#         with self.assertRaises(ValueError):
#             a[2:4] = b'\0'
#         self.assertRaises(ValueError, a.append, 3)
#         self.assertRaises(ValueError, a.extend, [5, 6])
#         with self.assertRaises(ValueError):
#             a += [5, 6]
# 
#     def test_optional_fixed_array(self):
#         optType = Optional(self.IntArray)
#         yes = optType(range(5))
#         no = optType()
#         self.assertIsInstance(yes, self.IntArray)
#         self.assertEqual(yes, [0, 1, 2, 3, 4])
#         self.assertEqual(no, None)
#         y_b = pack(yes)
#         n_b = pack(no)
#         self.assertEqual(y_b, b'\0\0\0\x01'+ b''.join((b'\0\0\0\0',
#                                                        b'\0\0\0\x01',
#                                                        b'\0\0\0\x02',
#                                                        b'\0\0\0\x03',
#                                                        b'\0\0\0\x04')))
#         self.assertEqual(n_b, b'\0\0\0\0')
#         self.assertEqual(unpack(optType, y_b), yes)
#         self.assertEqual(unpack(optType, n_b), no)
#         
#         
#         
# class TestVarArray(unittest.TestCase):
#     class IntArray(VarArray):
#         _element_type = Int32
#         _size = 15
#     
#     class StringArray(VarArray):
#         class MyString(String):
#             _size = 15
#         
#         _element_type = MyString
#         _size = 7
#         
#     def test_var_array_packing(self):
#         a = self.IntArray(range(4))
#         self.assertIsInstance(a, list)
#         self.assertEqual(a, [0, 1, 2, 3])
#         bp = pack(a)
#         self.assertEqual(bp, b'\0\0\0\x04\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03')
#         self.assertEqual(unpack(self.IntArray, bp), a)
#         a.append(4)
#         bp = pack(a)
#         self.assertEqual(bp, b'\0\0\0\x05\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03\0\0\0\4')
#         self.assertEqual(unpack(self.IntArray, bp), a)
#         
#         b = self.StringArray((b'hello', b'this', b'is', b'the', b'message'))
#         bp = pack(b)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x05',
#                                        b'\0\0\0\x05hello\0\0\0',
#                                        b'\0\0\0\x04this',
#                                        b'\0\0\0\x02is\0\0',
#                                        b'\0\0\0\x03the\0',
#                                        b'\0\0\0\x07message\0')))
#         self.assertEqual(unpack(self.StringArray, bp), b)
#     
#     def test_empty_var_array(self):
#         a = self.IntArray(())
#         self.assertEqual(a, [])
#         bp = pack(a)
#         self.assertEqual(bp, b'\0\0\0\0')
#         self.assertEqual(unpack(self.IntArray, bp), a)
#     
#     def test_fixed_array_errors(self):
#         self.assertRaises(ValueError, self.IntArray, range(20))
#         self.assertRaises(ValueError, self.StringArray,
#                           (b'a', b'b', b'c', b'd', b'this is way too long'))
#         a = self.IntArray(range(10))
#         a.extend(range(5))
#         self.assertEqual(a, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4])
#         with self.assertRaises(ValueError):
#             a.append(5)
#             
#     
#     def test_fixed_array_unpack_errors(self):
#         self.assertRaises(ValueError, unpack, self.IntArray,
#                           b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0')
#         self.assertRaises(ValueError, unpack, self.StringArray,
#                           b''.join((b'\0\0\0\x05',
#                                     b'\0\0\0\x05hello\0\0\0',
#                                     b'\0\0\0\x04this',
#                                     b'\0\0\0\x02is\0\0',
#                                     b'\0\0\0\x03the\0',
#                                     b'\0\0\0\x14message is too long.')))
#         
#     def test_var_array_class_construction(self):
#         my_cls = VarArrayType('my_cls', size=5, element_type=Int32)
#         self.assertTrue(issubclass(my_cls, VarArray))
#         self.assertTrue(VarArray in my_cls.__mro__)
#         a = my_cls(range(4))
#         bp = pack(a)
#         self.assertEqual(bp, b'\0\0\0\x04\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03')
#         self.assertEqual(unpack(my_cls, bp), a)
# 
#     def test_can_append_to_var_array(self):
#         a = self.IntArray([0, 1])
#         for b in [2, 3, 4]:
#             a.append(b)
#         self.assertEqual(a, [0, 1, 2, 3, 4])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x05',
#                                        b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\x02',
#                                        b'\0\0\0\x03',
#                                        b'\0\0\0\x04')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
# 
#     def test_can_extend_var_array(self):
#         a = self.IntArray([0, 1])
#         a.extend((2, 3, 4))
#         self.assertEqual(a, [0, 1, 2, 3, 4])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x05',
#                                        b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\x02',
#                                        b'\0\0\0\x03',
#                                        b'\0\0\0\x04')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
#     
#     def test_can_delete_item_from_var_array(self):
#         a = self.IntArray(range(5))
#         del a[2]
#         self.assertEqual(a, [0, 1, 3, 4])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x04',
#                                        b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\x03',
#                                        b'\0\0\0\x04')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
#         
#     def test_can_delete_slice_from_var_array(self):
#         a = self.IntArray(range(5))
#         del a[1:4]
#         self.assertEqual(a, [0, 4])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x02',
#                                        b'\0\0\0\0',
#                                        b'\0\0\0\x04')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
# 
#     def test_var_array_grows_too_large(self):
#         a = self.IntArray(range(4))
#         self.assertRaises(ValueError, a.extend, range(20))
#         with self.assertRaises(ValueError):
#             for c in range(20):
#                 a.append(c)
#         with self.assertRaises(ValueError):
#             a[0:0] = range(20)
#         with self.assertRaises(ValueError):
#             a[-1:] = range(20)
#         with self.assertRaises(ValueError):
#             a += range(20)
#     
#     def test_var_array_item_replacement(self):
#         a = self.IntArray(range(4))
#         a[2] = 255
#         self.assertEqual(a, [0, 1, 255, 3])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x04',
#                                        b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\xff',
#                                        b'\0\0\0\x03')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
#     
#     def test_var_array_augmented_addition(self):
#         a = self.IntArray(range(4))
#         a += range(4)
#         self.assertEqual(a, [0, 1, 2, 3, 0, 1, 2, 3])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x08',
#                                        b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\x02',
#                                        b'\0\0\0\x03',
#                                        b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\x02',
#                                        b'\0\0\0\x03')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
# 
#     def test_var_array_slice_replacement(self):
#         a = self.IntArray(range(5))
#         a[2:4] = [255, 256]
#         self.assertEqual(a, [0, 1, 255, 256, 4])
#         bp = pack(a)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x05',
#                                        b'\0\0\0\0',
#                                        b'\0\0\0\x01',
#                                        b'\0\0\0\xff',
#                                        b'\0\0\x01\0',
#                                        b'\0\0\0\x04')))
#         self.assertEqual(unpack(self.IntArray, bp), a)
# 
#     def test_optional_var_array(self):
#         optType = Optional(self.IntArray)
#         yes = optType(range(5))
#         no = optType()
#         self.assertIsInstance(yes, self.IntArray)
#         self.assertEqual(yes, [0, 1, 2, 3, 4])
#         self.assertEqual(no, None)
#         y_b = pack(yes)
#         n_b = pack(no)
#         self.assertEqual(y_b, b'\0\0\0\x01' +
#                               b'\0\0\0\x05' + 
#                               b''.join((b'\0\0\0\0',
#                                         b'\0\0\0\x01',
#                                         b'\0\0\0\x02',
#                                         b'\0\0\0\x03',
#                                         b'\0\0\0\x04')))
#         self.assertEqual(n_b, b'\0\0\0\0')
#         self.assertEqual(unpack(optType, y_b), yes)
#         self.assertEqual(unpack(optType, n_b), no)
#         
#         
#        
# class TestStructure(unittest.TestCase):
#     class SimpleStructure(Structure):
#         n = Int32
#         s = StringType('s', 5)
#         t = FixedArrayType('t', size=5, element_type=VarOpaqueType('x', 3))
#          
#     def test_simple_struct_by_keywords(self):
#         s = self.SimpleStructure(n=3, s=b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
#         self.assertEqual(s.n, 3)
#         self.assertEqual(s.s, b'hallo')
#         self.assertSequenceEqual(s.t, (b'abc', b'de', b'f', b'', b'ghi'))
#          
#         bp = pack(s)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x03',
#                                        b'\0\0\0\x05hallo\0\0\0',
#                                        b''.join((b'\0\0\0\x03abc\0',
#                                                  b'\0\0\0\x02de\0\0',
#                                                  b'\0\0\0\x01f\0\0\0',
#                                                  b'\0\0\0\0',
#                                                  b'\0\0\0\x03ghi\0'
#                                                  ))
#                                        ))
#                          )
#         self.assertEqual(unpack(self.SimpleStructure, bp), s)
#      
#     def test_simple_struct_by_arguments(self):
#         s = self.SimpleStructure(3, b'hallo', (b'abc', b'de', b'f', b'', b'ghi'))
#         self.assertEqual(s.n, 3)
#         self.assertEqual(s.s, b'hallo')
#         self.assertSequenceEqual(s.t, (b'abc', b'de', b'f', b'', b'ghi'))
#          
#         bp = pack(s)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x03',
#                                        b'\0\0\0\x05hallo\0\0\0',
#                                        b''.join((b'\0\0\0\x03abc\0',
#                                                  b'\0\0\0\x02de\0\0',
#                                                  b'\0\0\0\x01f\0\0\0',
#                                                  b'\0\0\0\0',
#                                                  b'\0\0\0\x03ghi\0'
#                                                  ))
#                                        ))
#                          )
#         self.assertEqual(unpack(self.SimpleStructure, bp), s)
#          
#          
#     def test_simple_struct_by_mixed_arguments_and_keywords(self):
#         s = self.SimpleStructure(3, b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
#         self.assertEqual(s.n, 3)
#         self.assertEqual(s.s, b'hallo')
#         self.assertSequenceEqual(s.t, (b'abc', b'de', b'f', b'', b'ghi'))
#          
#         bp = pack(s)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x03',
#                                        b'\0\0\0\x05hallo\0\0\0',
#                                        b''.join((b'\0\0\0\x03abc\0',
#                                                  b'\0\0\0\x02de\0\0',
#                                                  b'\0\0\0\x01f\0\0\0',
#                                                  b'\0\0\0\0',
#                                                  b'\0\0\0\x03ghi\0'
#                                                  ))
#                                        ))
#                          )
#         self.assertEqual(unpack(self.SimpleStructure, bp), s)
#  
#     def test_structure_type_construction(self):
#         c = StructureType('c',
#                           ('n', Int32),
#                           ('s', StringType('s', 5)),
#                           ('t', FixedArrayType('t', size=5,
#                                                element_type=VarOpaqueType('', 3))))
#         s = c(n=3, s=b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
#         bp = pack(s)
#         self.assertEqual(bp, b''.join((b'\0\0\0\x03',
#                                        b'\0\0\0\x05hallo\0\0\0',
#                                        b''.join((b'\0\0\0\x03abc\0',
#                                                  b'\0\0\0\x02de\0\0',
#                                                  b'\0\0\0\x01f\0\0\0',
#                                                  b'\0\0\0\0',
#                                                  b'\0\0\0\x03ghi\0'
#                                                  ))
#                                        ))
#                          )
#         self.assertEqual(unpack(c, bp), s)
# 
#     def test_simple_struct_component_replacement(self):
#         s = self.SimpleStructure(3, b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
#         s.n = 512
#         s.s = b'bye'
#         s.t = (b'123', b'45', b'6', b'78', b'90')
#         self.assertEqual(s.n, 512)
#         self.assertEqual(s.s, b'bye')
#         self.assertEqual(s.t, [b'123', b'45', b'6', b'78', b'90'])
#         bp = pack(s)
#         self.assertEqual(bp, b''.join((b'\0\0\x02\0',
#                                        b'\0\0\0\x03bye\0',
#                                        b''.join((b'\0\0\0\x03123\0',
#                                                  b'\0\0\0\x0245\0\0',
#                                                  b'\0\0\0\x016\0\0\0',
#                                                  b'\0\0\0\x0278\0\0',
#                                                  b'\0\0\0\x0290\0\0'
#                                                  ))
#                                        ))
#                          )
#         self.assertEqual(unpack(self.SimpleStructure, bp), s)
#          
#     def test_optional_struct(self):
#         myStruct = StructureType('myStruct',
#                                  ('n', Int32),
#                                  ('s', StringType('s', 5)),
#                                  ('t', FixedArrayType('t', size=5,
#                                                       element_type=VarOpaqueType('', 3))))
# 
#         optStruct = Optional(myStruct)
#         yes = optStruct(1, b'hallo', (b'a', b'bc', b'def', b'gh', b''))
#         no = optStruct(None)
#         self.assertIsInstance(yes, myStruct)
#         self.assertEqual(no, None)
#         
#         b_yes = pack(yes)
#         b_no = pack(no)
#         self.assertEqual(b_yes, b'\0\0\0\x01'
#                                 b'\0\0\0\x01'
#                                 b'\0\0\0\x05hallo\0\0\0'
#                                 b'\0\0\0\x01a\0\0\0'
#                                 b'\0\0\0\x02bc\0\0'
#                                 b'\0\0\0\x03def\0'
#                                 b'\0\0\0\x02gh\0\0'
#                                 b'\0\0\0\0')
#         self.assertEqual(b_no, b'\0\0\0\0')
#         self.assertEqual(unpack(optStruct, b_no), no)
# 
#  
# class TestUnion(unittest.TestCase):
#     class SimpleUnion(Union):
#         discriminant = ('discr', Int32)
#         variants = {1: None,
#                     2: ('flag', Boolean),
#                     3: StringType('name', 10),
#                     4: ('foo', Int32uType('bar')),
#                     'default': ('whatever', FixedOpaqueType('x', 4)),
#                     }
#       
#     SimpleUnionFromEnum = UnionType('SimpleUnionFromEnum',
#                                     discriminant=('discr', EnumerationType('discr', a=1, b=2, c=3)),
#                                     variants={1: None, 2: ('number', Int32), 3: ('logic', Boolean)})
#       
#     def test_simple_union_invalid_initialization(self):
#         self.assertRaises(ValueError, self.SimpleUnion, 18, b'random value')
#         self.assertRaises(ValueError, self.SimpleUnionFromEnum, 5, b'some value')
#           
#     def test_simple_union_from_enum(self):
#         a = self.SimpleUnionFromEnum(1, None)
#         b = self.SimpleUnionFromEnum(2, 12345)
#         c = self.SimpleUnionFromEnum(3, True)
#         self.assertEqual(a, None)
#         self.assertIsInstance(a, Void)
#         self.assertEqual(b, 12345)
#         self.assertIsInstance(b, Int32)
#         self.assertEqual(c, True)
#         self.assertIsInstance(c, Boolean)
#         
#         b_a = pack(a)
#         b_b = pack(b)
#         b_c = pack(c)
#         self.assertEqual(b_a, b'\0\0\0\x01')
#         self.assertEqual(b_b, b'\0\0\0\x02' + pack(Int32(12345)))
#         self.assertEqual(b_c, b'\0\0\0\x03\0\0\0\x01')
#         self.assertEqual(unpack(self.SimpleUnionFromEnum, b_a), a)
#         self.assertEqual(unpack(self.SimpleUnionFromEnum, b_b), b)
#         self.assertEqual(unpack(self.SimpleUnionFromEnum, b_c), c)
#         
#     def test_simple_union_1(self):
#         u = self.SimpleUnion(1, None)
#         self.assertIsInstance(u, Void)
#         self.assertEqual(u, None)
#         self.assertEqual(u.discr, 1)
#         self.assertEqual(u.name, '')
#           
#         bp = pack(u)
#         self.assertEqual(bp, b'\0\0\0\x01')
#         self.assertEqual(unpack(self.SimpleUnion, bp), u)
#           
#     def test_simple_union_2(self):
#         u = self.SimpleUnion(2, True)
#         self.assertIsInstance(u, Boolean)
#         self.assertEqual(u, True)
#         self.assertEqual(u.discr, 2)
#         self.assertEqual(u.name, 'flag')
#           
#         bp = pack(u)
#         self.assertEqual(bp, b'\0\0\0\x02\0\0\0\x01')
#         self.assertEqual(unpack(self.SimpleUnion, bp), u)
#           
#     def test_simple_union_3(self):
#         u = self.SimpleUnion(3, b'hallo')
#         self.assertIsInstance(u, String)
#         self.assertEqual(u, b'hallo')
#         self.assertEqual(u.discr, 3)
#         self.assertEqual(u.name, 'name')
#   
#         bp = pack(u)
#         self.assertEqual(bp, b'\0\0\0\x03\0\0\0\x05hallo\0\0\0')
#         self.assertEqual(unpack(self.SimpleUnion, bp), u)
#           
#     def test_simple_union_4(self):
#         u = self.SimpleUnion(4, 13)
#         self.assertIsInstance(u, Int32u)
#         self.assertEqual(u, 13)
#         self.assertEqual(u.discr, 4)
#         self.assertEqual(u.name, 'foo')
#           
#         bp = pack(u)
#         self.assertEqual(bp, b'\0\0\0\x04\0\0\0\x0d')
#         self.assertEqual(unpack(self.SimpleUnion, bp), u)
#           
#     def test_simple_union_default(self):
#         u = self.SimpleUnion(255, b'dumb')
#         self.assertIsInstance(u, FixedOpaque)
#         self.assertEqual(u, b'dumb')
#         self.assertEqual(u.discr, 255)
#         self.assertEqual(u.name, 'whatever')
#           
#         bp = pack(u)
#         self.assertEqual(bp, b'\0\0\0\xffdumb')
#         self.assertEqual(unpack(self.SimpleUnion, bp), u)
# 
#     def test_optional_union(self):
#         optType = Optional(self.SimpleUnion)
#         y_1 = optType(1, None)
#         y_2 = optType(2, True)
#         y_3 = optType(3, b'hallo')
#         y_4 = optType(4, 13)
#         y_5 = optType(5, b'dumb')
#         no = optType(None)
#         self.assertEqual(y_1, None)
#         self.assertIsInstance(y_2, Boolean)
#         self.assertEqual(y_2, True)
#         self.assertIsInstance(y_3, String)
#         self.assertEqual(y_3, b'hallo')
#         self.assertIsInstance(y_4, Int32u)
#         self.assertEqual(y_4, 13)
#         self.assertIsInstance(y_5, FixedOpaque)
#         self.assertEqual(y_5, b'dumb')
#         self.assertEqual(no, None)
#         
#         b_y1 = pack(y_1)
#         b_y2 = pack(y_2)
#         b_y3 = pack(y_3)
#         b_y4 = pack(y_4)
#         b_y5 = pack(y_5)
#         b_no = pack(no)
#         self.assertEqual(b_y1, b'\0\0\0\x01' b'\0\0\0\x01')
#         self.assertEqual(b_y2, b'\0\0\0\x01' b'\0\0\0\x02' b'\0\0\0\x01')
#         self.assertEqual(b_y3, b'\0\0\0\x01' b'\0\0\0\x03' b'\0\0\0\x05' b'hallo' b'\0\0\0')
#         self.assertEqual(b_y4, b'\0\0\0\x01' b'\0\0\0\x04' b'\0\0\0\x0d')
#         self.assertEqual(b_y5, b'\0\0\0\x01' b'\0\0\0\x05' b'dumb')
#         self.assertEqual(b_no, b'\0\0\0\0')
#         self.assertEqual(unpack(optType, b_y1), y_1)
#         self.assertEqual(unpack(optType, b_y2), y_2)
#         self.assertEqual(unpack(optType, b_y3), y_3)
#         self.assertEqual(unpack(optType, b_y4), y_4)
#         self.assertEqual(unpack(optType, b_y5), y_5)
#         self.assertEqual(unpack(optType, b_no), no)

             

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()