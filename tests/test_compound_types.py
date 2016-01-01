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
    
    def test_fixed_opaque_class_construction(self):
        my_cls = xdrlib2.FixedOpaqueType('my_cls', 5)
        self.assertTrue(issubclass(my_cls, xdrlib2.FixedOpaque))
        self.assertTrue(xdrlib2.FixedOpaque in my_cls.__mro__)
        blob = my_cls(b'\0\xff\xab\xcd\x01')
        bp = pack(blob)
        self.assertEqual(bp, b'\0\xff\xab\xcd\x01\0\0\0')
        self.assertEqual(unpack(my_cls, bp), blob)
    
    def test_fixed_opaque_with_size_0(self):
        my_cls = xdrlib2.FixedOpaqueType('my_cls', 0)
        blob = my_cls(())
        bp = pack(blob)
        self.assertEqual(bp, b'')
        self.assertEqual(unpack(my_cls, bp), blob)
     

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
    
    def test_var_opaque_class_construction(self):
        my_cls = xdrlib2.VarOpaqueType('my_cls', 9)
        self.assertTrue(issubclass(my_cls, xdrlib2.VarOpaque))
        self.assertTrue(xdrlib2.VarOpaque in my_cls.__mro__)
        blob = my_cls(b'\0\xff\xab\xcd\x01')
        bp = pack(blob)
        self.assertEqual(bp, b'\0\0\0\x05\0\xff\xab\xcd\x01\0\0\0')
        self.assertEqual(unpack(my_cls, bp), blob)
    
    def test_empty_var_opaque(self):
        blob = self.VarLengthOpaque(b'')
        bp = pack(blob)
        self.assertEqual(bp, b'\0\0\0\0')
        self.assertEqual(unpack(self.VarLengthOpaque, bp), blob)
     

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

    def test_string_class_construction(self):
        my_cls = xdrlib2.StringType('my_cls', 15)
        self.assertTrue(issubclass(my_cls, xdrlib2.String))
        self.assertTrue(xdrlib2.String in my_cls.__mro__)
        s = my_cls(b'Hello world!')
        bp = pack(s)
        self.assertEqual(bp, b'\0\0\0\x0cHello world!')
        self.assertEqual(unpack(my_cls, bp), s)
    
    def test_empty_string(self):
        s = self.MyString(b'')
        bp = pack(s)
        self.assertEqual(bp, b'\0\0\0\0')
        self.assertEqual(unpack(self.MyString, bp), s)
     

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

    def test_fixed_array_class_construction(self):
        my_cls = xdrlib2.FixedArrayType('my_cls', size=5, element_type=xdrlib2.Int32)
        self.assertTrue(issubclass(my_cls, xdrlib2.FixedArray))
        self.assertTrue(xdrlib2.FixedArray in my_cls.__mro__)
        a = my_cls(range(5))
        bp = pack(a)
        self.assertEqual(bp, b'\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03\0\0\0\x04')
        self.assertEqual(unpack(my_cls, bp), a)
    
    def test_fixed_array_size_0(self):
        my_cls = xdrlib2.FixedArrayType('my_cls', size=0, element_type=xdrlib2.Boolean)
        a = my_cls(())
        bp = pack(a)
        self.assertEqual(bp, b'')
        self.assertEqual(unpack(my_cls, bp), a)
     
        
        
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
    
    def test_empty_var_array(self):
        a = self.IntArray(())
        bp = pack(a)
        self.assertEqual(bp, b'\0\0\0\0')
        self.assertEqual(unpack(self.IntArray, bp), a)
    
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
        
    def test_var_array_class_construction(self):
        my_cls = xdrlib2.VarArrayType('my_cls', size=5, element_type=xdrlib2.Int32)
        self.assertTrue(issubclass(my_cls, xdrlib2.VarArray))
        self.assertTrue(xdrlib2.VarArray in my_cls.__mro__)
        a = my_cls(range(4))
        bp = pack(a)
        self.assertEqual(bp, b'\0\0\0\x04\0\0\0\0\0\0\0\x01\0\0\0\x02\0\0\0\x03')
        self.assertEqual(unpack(my_cls, bp), a)
        
       
class TestStructure(unittest.TestCase):
    class SimpleStructure(xdrlib2.Structure):
        n = xdrlib2.Int32
        s = xdrlib2.StringType('s', 5)
        t = xdrlib2.FixedArrayType('t', size=5, element_type=xdrlib2.VarOpaqueType('_', 3))
        
    def test_simple_struct(self):
        s = self.SimpleStructure(n=3, s=b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
        self.assertEqual(s.n, 3)
        self.assertEqual(s.s, b'hallo')
        self.assertSequenceEqual(s.t, (b'abc', b'de', b'f', b'', b'ghi'))
        
        bp = pack(s)
        self.assertEqual(bp, b''.join((b'\0\0\0\x03',
                                       b'\0\0\0\x05hallo\0\0\0',
                                       b''.join((b'\0\0\0\x03abc\0',
                                                 b'\0\0\0\x02de\0\0',
                                                 b'\0\0\0\x01f\0\0\0',
                                                 b'\0\0\0\0',
                                                 b'\0\0\0\x03ghi\0'
                                                 ))
                                       ))
                         )
        self.assertEqual(unpack(self.SimpleStructure, bp), s)

class TestVoid(unittest.TestCase):
    def test_void(self):
        v1 = xdrlib2.Void()
        v2 = xdrlib2.Void(None)
        self.assertEqual(v1, v2)
        self.assertEqual(v1, None)
        
        bp1 = pack(v1)
        bp2 = pack(v2)
        self.assertEqual(bp1, bp2)
        self.assertEqual(bp1, b'')
        self.assertEqual(unpack(xdrlib2.Void, bp1), v2)
        
class TestUnion(unittest.TestCase):
    class SimpleUnion(xdrlib2.Union):
        _discriminant = xdrlib2.Int32Type('discr')
        _variants = {1: None,
                     2: ('number', xdrlib2.Int64),
                     3: xdrlib2.StringType('string', 10),
                     4: ('foo', xdrlib2.Int32uType('bar')),
                     None: ('default', xdrlib2.FixedOpaqueType('_', 4))
                     }
    
    class SimpleUnionFromEnum(xdrlib2.Union):
        _discriminant = xdrlib2.EnumerationType('discr', a=1, b=2, c=3)
        _variants = {1: None,
                     2: ('number', xdrlib2.Int32),
                     3: ('logic', xdrlib2.Boolean)}
        
    
    def test_simple_union_invalid_initialization(self):
        self.assertRaises(ValueError, self.SimpleUnion, unknown=18)
        self.assertRaises(ValueError, self.SimpleUnionFromEnum, 5)
        
    
    def test_simple_union_1(self):
        u = self.SimpleUnion(1, None)
        
        self.assertEqual(u.discr, 1)
        self.assertEqual(u[1], None)
        
        with self.assertRaises(AttributeError):
            u.number
        with self.assertRaises(KeyError):
            u[3]
        
        bp = pack(u)
        self.assertEqual(bp, b'\0\0\0\x01')
        self.assertEqual(unpack(self.SimpleUnion, bp), u)
        
    def test_simple_union_2(self):
        u = self.SimpleUnion(number=0xffeeddccbbaa)
        
        self.assertEqual(u.discr, 2)
        self.assertEqual(u[2], 0xffeeddccbbaa)
        self.assertEqual(u.number, 0xffeeddccbbaa)
        
        bp = pack(u)
        self.assertEqual(bp, b'\0\0\0\x02\0\0\xff\xee\xdd\xcc\xbb\xaa')
        self.assertEqual(unpack(self.SimpleUnion, bp), u)
        
    def test_simple_union_3(self):
        u = self.SimpleUnion(string=b'hallo')
        
        self.assertEqual(u.discr, 3)
        self.assertEqual(u[3], b'hallo')
        self.assertEqual(u.string, b'hallo')

        bp = pack(u)
        
        self.assertEqual(bp, b'\0\0\0\x03\0\0\0\x05hallo\0\0\0')
        self.assertEqual(unpack(self.SimpleUnion, bp), u)
        
    def test_simple_union_4(self):
        u = self.SimpleUnion('foo', 13)
        
        self.assertEqual(u.discr, 4)
        self.assertEqual(u[4], 13)
        self.assertEqual(u.foo, 13)
        
        bp = pack(u)
        self.assertEqual(bp, b'\0\0\0\x04\0\0\0\x0d')
        self.assertEqual(unpack(self.SimpleUnion, bp), u)
        
    def test_simple_union_default(self):
        u = self.SimpleUnion(255, b'dumb')
        
        self.assertEqual(u.discr, 255)
        self.assertEqual(u[255], b'dumb')
        with self.assertRaises(KeyError):
            u[100]
        self.assertEqual(u.default, b'dumb')
        
        bp = pack(u)
        self.assertEqual(bp, b'\0\0\0\xffdumb')
        self.assertEqual(unpack(self.SimpleUnion, bp), u)
           
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()