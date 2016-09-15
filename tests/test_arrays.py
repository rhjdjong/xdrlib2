'''
Created on 2 sep. 2016

@author: Ruud
'''
import unittest

from xdrlib2 import *
from xdrlib2.xdr_types import _padding

class TestFixedArray(unittest.TestCase):
    class IntArray(FixedArray):
        size = 5
        type = Int32
    
    class StringArray(FixedArray):
        size = 3
        type = String(size=7)
        
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
        
        self.assertEqual(i_bytes, b''.join(encode(Int32(i)) for i in int_list))
        self.assertEqual(s_bytes, b''.join(b''.join((encode(Int32u(len(s))),
                                                     s,
                                                     _padding(len(s))))
                                           for s in str_list)
                         )
        
        i_decoded = decode(self.IntArray, i_bytes)
        s_decoded = decode(self.StringArray, s_bytes)
        self.assertEqual(i_arr, i_decoded)
        self.assertEqual(s_arr, s_decoded)
        
    def test_fixed_array_requries_correctly_sized_arguments(self):
        self.assertRaises(ValueError, self.IntArray, (1, 2, 3))
        self.assertRaises(ValueError, self.StringArray, (b'a', b'bc', b'def', b'ghij', b'klmno'))
    
    def test_fixed_array_decode_errors(self):
        int_list = [1, 2, 3, 4]
        str_list = [b'a', b'bc', b'def', b'ghij', b'klmno']
        self.assertRaises(ValueError, decode, self.IntArray,
                          b''.join(encode(Int32(i)) for i in int_list))
        self.assertRaises(ValueError, decode, self.StringArray,
                          b''.join(b''.join((encode(Int32u(len(s))),
                                             s,
                                             _padding(len(s))))
                                   for s in str_list))
    
    def test_fixed_array_requires_correct_type(self):
        self.assertRaises(ValueError, self.IntArray, (b'a', b'bc', b'def', b'ghij', b'klmno'))
        self.assertRaises(ValueError, self.StringArray, (1, 2, 3))

    def test_fixed_array_class_construction(self):
        my_cls = FixedArray(size=5, type=Boolean)
        self.assertTrue(issubclass(my_cls, FixedArray))
        self.assertTrue(FixedArray in my_cls.__mro__)
        arg_list = [False, True, True, False, True]
        x = my_cls(arg_list)
        self.assertSequenceEqual(x, arg_list)
        self.assertIsInstance(x, my_cls)
        self.assertTrue(all(isinstance(a, x._type) for a in x))
        x_bytes = encode(x)
        self.assertEqual(x_bytes, b''.join(encode(Boolean(b)) for b in arg_list))
        self.assertEqual(decode(my_cls, x_bytes), x)

    def test_fixed_array_with_size_0(self):
        my_cls = FixedArray(size=0, type=Int32)
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

    def test_optional_fixed_array(self):
        optType = Optional(self.IntArray)
        yes = optType(range(5))
        no = optType()
        self.assertIsInstance(yes, self.IntArray)
        self.assertEqual(yes, [0, 1, 2, 3, 4])
        self.assertEqual(no, None)
        y_b = encode(yes)
        n_b = encode(no)
        self.assertEqual(y_b, encode(TRUE) + b''.join(encode(Int32(x)) for x in range(5))) # @UndefinedVariable
        self.assertEqual(n_b, encode(FALSE)) # @UndefinedVariable
        self.assertEqual(decode(optType, y_b), yes)
        self.assertEqual(decode(optType, n_b), no)

    def test_explicit_subclassing(self):
        subcls = FixedArray.typedef(type=Int32, size=5)
        self.assertTrue(issubclass(subcls, FixedArray))
        x = subcls((1, 2, 3, 4, 5))
        self.assertIsInstance(x, FixedArray)
        self.assertEqual(encode(x), b''.join(encode(Int32(x)) for x in (1, 2, 3, 4, 5)))
             
class TestVarArray(unittest.TestCase):
    class IntArray(VarArray):
        size = 5
        type = Int32
    
    class StringArray(VarArray):
        size = 3
        type = String(size=7)
        
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
        
        self.assertEqual(i_bytes, encode(Int32u(len(int_list))) + b''.join(encode(Int32(i)) for i in int_list))
        self.assertEqual(s_bytes, encode(Int32u(len(str_list))) + b''.join(b''.join((encode(Int32u(len(s))),
                                                                                     s,
                                                                                     _padding(len(s))))
                                                                           for s in str_list))
        
        i_decoded = decode(self.IntArray, i_bytes)
        s_decoded = decode(self.StringArray, s_bytes)
        self.assertEqual(i_arr, i_decoded)
        self.assertEqual(s_arr, s_decoded)
        
    def test_var_array_requries_correctly_sized_arguments(self):
        self.assertRaises(ValueError, self.IntArray, (1, 2, 3, 4, 5, 6))
        self.assertRaises(ValueError, self.StringArray, (b'a', b'bc', b'def', b'ghij', b'klmno'))
    
    def test_var_array_decode_errors(self):
        self.assertRaises(ValueError, decode, self.IntArray,
                          encode(Int32u(6)) + b''.join(encode(Int32(i)) for i in range(1, 6)))
        self.assertRaises(ValueError, decode, self.StringArray,
                          encode(Int32u(5)) + b''.join(b''.join((encode(Int32u(len(s))),
                                                                 s,
                                                                 _padding(len(s))))
                                                       for s in [b'a', b'bc', b'def', b'ghij', b'klmno']))

    
    def test_var_array_requires_correct_type(self):
        self.assertRaises(ValueError, self.IntArray, (b'a', b'bc', b'def', b'ghij', b'klmno'))
        self.assertRaises(ValueError, self.StringArray, (1, 2, 3))

    def test_var_array_class_construction(self):
        my_cls = VarArray(size=5, type=Boolean)
        self.assertTrue(issubclass(my_cls, VarArray))
        self.assertTrue(VarArray in my_cls.__mro__)
        arg_list = [False, True]
        x = my_cls(arg_list)
        self.assertSequenceEqual(x, arg_list)
        self.assertIsInstance(x, my_cls)
        self.assertTrue(all(isinstance(a, x._type) for a in x))
        x_bytes = encode(x)
        self.assertEqual(x_bytes, encode(Int32u(len(arg_list))) + b''.join((encode(Boolean(x)) for x in arg_list)))
        self.assertEqual(decode(my_cls, x_bytes), x)

    def test_var_array_with_size_0(self):
        my_cls = VarArray(size=0, type=Int32)
        x = my_cls(())
        self.assertIsInstance(x, my_cls)
        self.assertSequenceEqual(x, [])
        x_bytes = encode(x)
        self.assertEqual(x_bytes, encode(Int32u(0)))
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
    
    def test_optional_var_array(self):
        optType = Optional(self.IntArray)
        yes = optType(range(5))
        no = optType()
        self.assertIsInstance(yes, self.IntArray)
        self.assertEqual(yes, [0, 1, 2, 3, 4])
        self.assertEqual(no, None)
        y_b = encode(yes)
        n_b = encode(no)
        self.assertEqual(y_b, encode(TRUE) + # @UndefinedVariable
                              encode(Int32u(5)) +
                              b''.join(encode(Int32(x)) for x in range(5)))
        self.assertEqual(n_b, encode(FALSE)) # @UndefinedVariable
        self.assertEqual(decode(optType, y_b), yes)
        self.assertEqual(decode(optType, n_b), no)

    def test_explicit_subclassing(self):
        subcls = VarArray.typedef(type=Int32, size=5)
        self.assertTrue(issubclass(subcls, VarArray))
        x = subcls((1, 2, 3))
        self.assertIsInstance(x, VarArray)
        self.assertEqual(encode(x), encode(Int32u(3)) +
                                    b''.join(encode(Int32(x)) for x in (1, 2, 3)))
    
   
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()