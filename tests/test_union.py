'''
Created on 5 sep. 2016

@author: Ruud
'''
import unittest

from xdrlib2 import *

class TestUnion(unittest.TestCase):
    class SimpleUnion(Union):
        switch = ('discr', Int32)
        case = {1: None,
                2: ('flag', Boolean),
                3: String.typedef('name', 10),
                4: ('foo', Int32u.typedef('bar')),
                'default': ('whatever', FixedBytes.typedef('x', 4)),
                }
       
    SimpleUnionFromEnum = Union.typedef('SimpleUnionFromEnum',
                                        switch=('discr', Enumeration.typedef('discr', a=1, b=2, c=3)),
                                        case={1: None, 2: ('number', Int32), 3: ('logic', Boolean)})
       
    def test_simple_union_invalid_initialization(self):
        self.assertRaises(ValueError, self.SimpleUnion, 18, b'random value')
        self.assertRaises(ValueError, self.SimpleUnionFromEnum, 5, b'some value')
            
    def test_simple_union_from_enum(self):
        a = self.SimpleUnionFromEnum(1, None)
        b = self.SimpleUnionFromEnum(2, 12345)
        c = self.SimpleUnionFromEnum(3, True)
        self.assertEqual(a, (1, None))
        self.assertEqual(a.switch, 1)
        self.assertEqual(a.case, None)
        self.assertIsInstance(a.case, Void)
        self.assertEqual(b, (2, 12345))
        self.assertIsInstance(b.case, Int32)
        self.assertEqual(c, (3, True))
        self.assertIsInstance(c.case, Boolean)
          
        b_a = encode(a)
        b_b = encode(b)
        b_c = encode(c)
        self.assertEqual(b_a, b'\0\0\0\x01')
        self.assertEqual(b_b, b'\0\0\0\x02' + encode(Int32(12345)))
        self.assertEqual(b_c, b'\0\0\0\x03\0\0\0\x01')
        self.assertEqual(decode(self.SimpleUnionFromEnum, b_a), a)
        self.assertEqual(decode(self.SimpleUnionFromEnum, b_b), b)
        self.assertEqual(decode(self.SimpleUnionFromEnum, b_c), c)
          
    def test_simple_union_1(self):
        u = self.SimpleUnion(1, None)
        self.assertEqual(u, (1, None))
        self.assertIsInstance(u.case, Void)
        self.assertEqual(u.case, None)
        self.assertEqual(u.switch, 1)
            
        bp = encode(u)
        self.assertEqual(bp, b'\0\0\0\x01')
        self.assertEqual(decode(self.SimpleUnion, bp), u)
            
    def test_simple_union_2(self):
        u = self.SimpleUnion(2, True)
        self.assertEqual(u, (2, True))
        self.assertIsInstance(u.case, Boolean)
        self.assertEqual(u.case, True)
        self.assertEqual(u.switch, 2)
            
        bp = encode(u)
        self.assertEqual(bp, b'\0\0\0\x02\0\0\0\x01')
        self.assertEqual(decode(self.SimpleUnion, bp), u)
            
    def test_simple_union_3(self):
        u = self.SimpleUnion(3, b'hallo')
        self.assertEqual(u, (3, b'hallo'))
        self.assertIsInstance(u.case, String)
        self.assertEqual(u.case, b'hallo')
        self.assertEqual(u.switch, 3)
    
        bp = encode(u)
        self.assertEqual(bp, b'\0\0\0\x03\0\0\0\x05hallo\0\0\0')
        self.assertEqual(decode(self.SimpleUnion, bp), u)
            
    def test_simple_union_4(self):
        u = self.SimpleUnion(4, 13)
        self.assertEqual(u, (4, 13))
        self.assertIsInstance(u.case, Int32u)
        self.assertEqual(u.case, 13)
        self.assertEqual(u.switch, 4)
            
        bp = encode(u)
        self.assertEqual(bp, b'\0\0\0\x04\0\0\0\x0d')
        self.assertEqual(decode(self.SimpleUnion, bp), u)
            
    def test_simple_union_default(self):
        u = self.SimpleUnion(255, b'dumb')
        self.assertEqual(u, (255, b'dumb'))
        self.assertIsInstance(u.case, FixedBytes)
        self.assertEqual(u.case, b'dumb')
        self.assertEqual(u.switch, 255)
            
        bp = encode(u)
        self.assertEqual(bp, b'\0\0\0\xffdumb')
        self.assertEqual(decode(self.SimpleUnion, bp), u)
  
    def test_optional_union(self):
        optType = Optional(self.SimpleUnion)
        y_1 = optType(1, None)
        y_2 = optType(2, True)
        y_3 = optType(3, b'hallo')
        y_4 = optType(4, 13)
        y_5 = optType(5, b'dumb')
        no = optType(None)
        self.assertEqual(y_1, (1, None))
        self.assertIsInstance(y_2.case, Boolean)
        self.assertEqual(y_2, (2, True))
        self.assertIsInstance(y_3.case, String)
        self.assertEqual(y_3, (3, b'hallo'))
        self.assertIsInstance(y_4.case, Int32u)
        self.assertEqual(y_4, (4, 13))
        self.assertIsInstance(y_5.case, FixedBytes)
        self.assertEqual(y_5, (5, b'dumb'))
        self.assertEqual(no, None)
          
        b_y1 = encode(y_1)
        b_y2 = encode(y_2)
        b_y3 = encode(y_3)
        b_y4 = encode(y_4)
        b_y5 = encode(y_5)
        b_no = encode(no)
        self.assertEqual(b_y1, b'\0\0\0\x01' b'\0\0\0\x01')
        self.assertEqual(b_y2, b'\0\0\0\x01' b'\0\0\0\x02' b'\0\0\0\x01')
        self.assertEqual(b_y3, b'\0\0\0\x01' b'\0\0\0\x03' b'\0\0\0\x05' b'hallo' b'\0\0\0')
        self.assertEqual(b_y4, b'\0\0\0\x01' b'\0\0\0\x04' b'\0\0\0\x0d')
        self.assertEqual(b_y5, b'\0\0\0\x01' b'\0\0\0\x05' b'dumb')
        self.assertEqual(b_no, b'\0\0\0\0')
        self.assertEqual(decode(optType, b_y1), y_1)
        self.assertEqual(decode(optType, b_y2), y_2)
        self.assertEqual(decode(optType, b_y3), y_3)
        self.assertEqual(decode(optType, b_y4), y_4)
        self.assertEqual(decode(optType, b_y5), y_5)
        self.assertEqual(decode(optType, b_no), no)
    
    def test_union_values_can_be_accessed_by_name(self):
        a = self.SimpleUnionFromEnum(1, None)
        b = self.SimpleUnionFromEnum(2, 12345)
        c = self.SimpleUnionFromEnum(3, True)
        
        self.assertEqual(a.discr, 1)
        self.assertEqual(b.number, 12345)
        self.assertEqual(c.logic, True)
        
        with self.assertRaises(AttributeError):
            a.invalid_name
        
        with self.assertRaises(AttributeError):
            b.logic
    
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()