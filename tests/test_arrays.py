'''
Created on 2 sep. 2016

@author: Ruud
'''
import unittest

from xdrlib2 import *

class TestFixedArray(unittest.TestCase):
    class IntArray(FixedArray):
        size = 5
        type = Int32
    
    class StringArray(FixedArray):
        size = 3
        type = String.typedef('MyString', 7)
        
    def test_default_instantiation(self):
        x = self.IntArray()
        self.assertIsInstance(x, self.IntArray)
        self.assertSequenceEqual(x, [0, 0, 0, 0, 0])
        self.assertTrue(all(isinstance(a, x._type) for a in x))
        
        x = self.StringArray()
        self.assertIsInstance(x, self.StringArray)
        self.assertSequenceEqual(x, [b'', b'', b''])
        self.assertTrue(all(isinstance(a, x._type) for a in x))
        
    def test_encoding_and_decoding(self):
        int_list = [1, 2, 3, 4, 5]
        str_list = [b'a', b'bc', b'def']
        
        i_arr = self.IntArray(int_list)
        s_arr = self.StringArray(str_list)
        
        self.assertTrue(all(isinstance(a, i_arr._type) for a in i_arr))
        self.assertTrue(all(isinstance(a, s_arr._type) for a in s_arr))

        i_bytes = encode(i_arr)
        s_bytes = encode(s_arr)
        
        self.assertEqual(i_bytes, b'\0\0\0\x01'
                                  b'\0\0\0\x02'
                                  b'\0\0\0\x03'
                                  b'\0\0\0\x04'
                                  b'\0\0\0\x05')
        self.assertEqual(s_bytes, b'\0\0\0\x01' b'a\0\0\0'
                                  b'\0\0\0\x02' b'bc\0\0'
                                  b'\0\0\0\x03' b'def\0')
        
        i_decoded = decode(self.IntArray, i_bytes)
        s_decoded = decode(self.StringArray, s_bytes)
        self.assertEqual(i_arr, i_decoded)
        self.assertEqual(s_arr, s_decoded)
        
    def test_fixed_array_requries_correctly_sized_arguments(self):
        self.assertRaises(ValueError, self.IntArray, (1, 2, 3))
        self.assertRaises(ValueError, self.StringArray, (b'a', b'bc', b'def', b'ghij', b'klmno'))
    
    def test_fixed_array_decode_errors(self):
        self.assertRaises(ValueError, decode, self.IntArray, b'\0\0\0\x01'
                                                             b'\0\0\0\x02'
                                                             b'\0\0\0\x03'
                                                             b'\0\0\0\x04')
        self.assertRaises(ValueError, decode, self.StringArray, b'\0\0\0\x01' b'a\0\0\0'
                                                                b'\0\0\0\x02' b'bc\0\0'
                                                                b'\0\0\0\x03' b'def\0'
                                                                b'\0\0\0\x04' b'ghij'
                                                                b'\0\0\0\x05' b'klmno\0\0\0')
    
    def test_fixed_array_requires_correct_type(self):
        self.assertRaises(ValueError, self.IntArray, (b'a', b'bc', b'def', b'ghij', b'klmno'))
        self.assertRaises(ValueError, self.StringArray, (1, 2, 3))

    def test_fixed_array_class_construction(self):
        my_cls = FixedArray.typedef('my_cls', size=5, type=Boolean)
        self.assertTrue(issubclass(my_cls, FixedArray))
        self.assertTrue(FixedArray in my_cls.__mro__)
        arg_list = [False, True, True, False, True]
        x = my_cls(arg_list)
        self.assertSequenceEqual(x, arg_list)
        self.assertIsInstance(x, my_cls)
        self.assertTrue(all(isinstance(a, x._type) for a in x))
        x_bytes = encode(x)
        self.assertEqual(x_bytes, b'\0\0\0\0'
                                  b'\0\0\0\x01'
                                  b'\0\0\0\x01'
                                  b'\0\0\0\0'
                                  b'\0\0\0\x01')
        self.assertEqual(decode(my_cls, x_bytes), x)

    def test_fixed_array_with_size_0(self):
        my_cls = FixedArray.typedef('my_cls', size=0, type=Int32)
        x = my_cls(())
        self.assertIsInstance(x, my_cls)
        self.assertSequenceEqual(x, [])
        x_bytes = encode(x)
        self.assertEqual(x_bytes, b'')
        self.assertEqual(decode(my_cls, x_bytes), x)

    def test_fixed_array_item_replacement(self):
        arg_list = [0, 1, 2, 3, 4]
        x = self.IntArray(arg_list)
        x[2] = 10
        self.assertEqual(x, [0, 1, 10, 3, 4])
        self.assertTrue(all(isinstance(a, x._type) for a in x))

    def test_fixed_array_slice_replacement(self):
        arg_list = [0, 1, 2, 3, 4]
        x = self.IntArray(arg_list)
        x[2:4] = 10, 11
        self.assertEqual(x, [0, 1, 10, 11, 4])
        self.assertTrue(all(isinstance(a, x._type) for a in x))

    def test_fixed_array_size_change_fails(self):
        arg_list = [0, 1, 2, 3, 4]
        x = self.IntArray(arg_list)
        with self.assertRaises(ValueError):
            del x[2]
        with self.assertRaises(ValueError):
            x[2:4] = [3]
        self.assertRaises(ValueError, x.append, 3)
        self.assertRaises(ValueError, x.extend, [5, 6])
        with self.assertRaises(ValueError):
            x += [5, 6]


class TestVarArray(unittest.TestCase):
    class IntArray(VarArray):
        size = 5
        type = Int32
    
    class StringArray(VarArray):
        size = 3
        type = String.typedef('MyString', 7)
        
    def test_default_instantiation(self):
        x = self.IntArray()
        self.assertIsInstance(x, self.IntArray)
        self.assertSequenceEqual(x, [])
        
        x = self.StringArray()
        self.assertIsInstance(x, self.StringArray)
        self.assertSequenceEqual(x, [])
        
    def test_encoding_and_decoding(self):
        int_list = [1, 2, 3]
        str_list = [b'a', b'bc']
        
        i_arr = self.IntArray(int_list)
        s_arr = self.StringArray(str_list)
        self.assertTrue(all(isinstance(a, i_arr._type) for a in i_arr))
        self.assertTrue(all(isinstance(a, s_arr._type) for a in s_arr))
        
        i_bytes = encode(i_arr)
        s_bytes = encode(s_arr)
        
        self.assertEqual(i_bytes, b'\0\0\0\x03'
                                  b'\0\0\0\x01'
                                  b'\0\0\0\x02'
                                  b'\0\0\0\x03')
        self.assertEqual(s_bytes, b'\0\0\0\x02'
                                  b'\0\0\0\x01' b'a\0\0\0'
                                  b'\0\0\0\x02' b'bc\0\0')
        
        i_decoded = decode(self.IntArray, i_bytes)
        s_decoded = decode(self.StringArray, s_bytes)
        self.assertEqual(i_arr, i_decoded)
        self.assertEqual(s_arr, s_decoded)
        
    def test_var_array_requries_correctly_sized_arguments(self):
        self.assertRaises(ValueError, self.IntArray, (1, 2, 3, 4, 5, 6))
        self.assertRaises(ValueError, self.StringArray, (b'a', b'bc', b'def', b'ghij', b'klmno'))
    
    def test_var_array_decode_errors(self):
        self.assertRaises(ValueError, decode, self.IntArray, b'\0\0\0\x06'
                                                             b'\0\0\0\x01'
                                                             b'\0\0\0\x02'
                                                             b'\0\0\0\x03'
                                                             b'\0\0\0\x04'
                                                             b'\0\0\0\x05'
                                                             b'\0\0\0\x06')
        self.assertRaises(ValueError, decode, self.StringArray, b'\0\0\0\x05'
                                                                b'\0\0\0\x01' b'a\0\0\0'
                                                                b'\0\0\0\x02' b'bc\0\0'
                                                                b'\0\0\0\x03' b'def\0'
                                                                b'\0\0\0\x04' b'ghij'
                                                                b'\0\0\0\x05' b'klmno\0\0\0')
    
    def test_var_array_requires_correct_type(self):
        self.assertRaises(ValueError, self.IntArray, (b'a', b'bc', b'def', b'ghij', b'klmno'))
        self.assertRaises(ValueError, self.StringArray, (1, 2, 3))

    def test_var_array_class_construction(self):
        my_cls = VarArray.typedef('my_cls', size=5, type=Boolean)
        self.assertTrue(issubclass(my_cls, VarArray))
        self.assertTrue(VarArray in my_cls.__mro__)
        arg_list = [False, True]
        x = my_cls(arg_list)
        self.assertSequenceEqual(x, arg_list)
        self.assertIsInstance(x, my_cls)
        self.assertTrue(all(isinstance(a, x._type) for a in x))
        x_bytes = encode(x)
        self.assertEqual(x_bytes, b'\0\0\0\x02'
                                  b'\0\0\0\x00'
                                  b'\0\0\0\x01')
        self.assertEqual(decode(my_cls, x_bytes), x)

    def test_var_array_with_size_0(self):
        my_cls = VarArray.typedef('my_cls', size=0, type=Int32)
        x = my_cls(())
        self.assertIsInstance(x, my_cls)
        self.assertSequenceEqual(x, [])
        x_bytes = encode(x)
        self.assertEqual(x_bytes, b'\0\0\0\0')
        self.assertEqual(decode(my_cls, x_bytes), x)

    def test_var_array_item_replacement(self):
        arg_list = [0, 1, 2]
        x = self.IntArray(arg_list)
        x[1] = 10
        self.assertEqual(x, [0, 10, 2])
        self.assertTrue(all(isinstance(a, x._type) for a in x))

    def test_var_array_slice_replacement(self):
        arg_list = [0, 1, 2, 3, 4]
        x = self.IntArray(arg_list)
        x[2:4] = 10, 11
        self.assertEqual(x, [0, 1, 10, 11, 4])
        self.assertTrue(all(isinstance(a, x._type) for a in x))

    def test_can_append_to_var_array(self):
        arg_list = [0, 1, 2]
        x = self.IntArray(arg_list)
        for y in [3, 4]:
            x.append(y)
        self.assertEqual(x, [0, 1, 2, 3, 4])
        self.assertTrue(all(isinstance(a, x._type) for a in x))
 
    def test_can_extend_var_array(self):
        arg_list = [0, 1, 2]
        x = self.IntArray(arg_list)
        x.extend([3, 4])
        self.assertEqual(x, [0, 1, 2, 3, 4])
        self.assertTrue(all(isinstance(a, x._type) for a in x))
     
    def test_can_delete_item_from_var_array(self):
        arg_list = [0, 1, 2, 3, 4]
        x = self.IntArray(arg_list)
        del x[3]
        self.assertEqual(x, [0, 1, 2, 4])
         
    def test_can_delete_slice_from_var_array(self):
        arg_list = [0, 1, 2, 3, 4]
        x = self.IntArray(arg_list)
        del x[1:3]
        self.assertEqual(x, [0, 3, 4])
        
    def test_var_array_size_change_fails_if_max_size_exceeded(self):
        arg_list = [0, 1, 2, 3, 4]
        x = self.IntArray(arg_list)
        with self.assertRaises(ValueError):
            x[2:4] = [3, 4, 5]
        self.assertRaises(ValueError, x.append, 3)
        self.assertRaises(ValueError, x.extend, [5, 6])
        with self.assertRaises(ValueError):
            x += [5, 6]
    
    
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()