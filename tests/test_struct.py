'''
Created on 4 sep. 2016

@author: Ruud
'''
import unittest

from xdrlib2 import *


class TestStructure(unittest.TestCase):
    class SimpleStructure(Structure):
        n = Int32
        s = String.typedef('s', 5)
        t = FixedArray.typedef('t', size=5, type=VarBytes.typedef('x', 3))
    
    def test_simple_struct_by_keywords(self):
        s = self.SimpleStructure(n=3, s=b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
        self.assertEqual(s.n, 3)
        self.assertEqual(s.s, b'hallo')
        self.assertSequenceEqual(s.t, (b'abc', b'de', b'f', b'', b'ghi'))
          
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x03'
                             b'\0\0\0\x05' b'hallo\0\0\0'
                             b'\0\0\0\x03' b'abc\0'
                             b'\0\0\0\x02' b'de\0\0'
                             b'\0\0\0\x01' b'f\0\0\0'
                             b'\0\0\0\0'
                             b'\0\0\0\x03' b'ghi\0'
                         )
        self.assertEqual(decode(self.SimpleStructure, bp), s)
      
    def test_simple_struct_by_arguments(self):
        s = self.SimpleStructure(3, b'hallo', (b'abc', b'de', b'f', b'', b'ghi'))
        self.assertEqual(s.n, 3)
        self.assertEqual(s.s, b'hallo')
        self.assertSequenceEqual(s.t, (b'abc', b'de', b'f', b'', b'ghi'))
          
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x03'
                             b'\0\0\0\x05' b'hallo\0\0\0'
                             b'\0\0\0\x03' b'abc\0'
                             b'\0\0\0\x02' b'de\0\0'
                             b'\0\0\0\x01' b'f\0\0\0'
                             b'\0\0\0\0'
                             b'\0\0\0\x03' b'ghi\0'
                         )
        self.assertEqual(decode(self.SimpleStructure, bp), s)
          
          
    def test_simple_struct_by_mixed_arguments_and_keywords(self):
        s = self.SimpleStructure(3, b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
        self.assertEqual(s.n, 3)
        self.assertEqual(s.s, b'hallo')
        self.assertSequenceEqual(s.t, (b'abc', b'de', b'f', b'', b'ghi'))
          
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x03'
                             b'\0\0\0\x05' b'hallo\0\0\0'
                             b'\0\0\0\x03' b'abc\0'
                             b'\0\0\0\x02' b'de\0\0'
                             b'\0\0\0\x01' b'f\0\0\0'
                             b'\0\0\0\0'
                             b'\0\0\0\x03' b'ghi\0'
                         )
        self.assertEqual(decode(self.SimpleStructure, bp), s)
  
    def test_structure_type_construction(self):
        c = Structure.typedef('c',
                              ('n', Int32),
                              ('s', String.typedef('s', 5)),
                              ('t', FixedArray.typedef('t', size=5,
                                                       type=VarBytes.typedef('', 3))))
        s = c(n=3, s=b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\0\x03'
                             b'\0\0\0\x05' b'hallo\0\0\0'
                             b'\0\0\0\x03' b'abc\0'
                             b'\0\0\0\x02' b'de\0\0'
                             b'\0\0\0\x01' b'f\0\0\0'
                             b'\0\0\0\0'
                             b'\0\0\0\x03' b'ghi\0'
                         )
        self.assertEqual(decode(c, bp), s)
 
    def test_simple_struct_component_replacement(self):
        s = self.SimpleStructure(3, b'hallo', t=(b'abc', b'de', b'f', b'', b'ghi'))
        s.n = 512
        s.s = b'bye'
        s.t = (b'123', b'45', b'6', b'78', b'90')
        self.assertEqual(s.n, 512)
        self.assertEqual(s.s, b'bye')
        self.assertEqual(s.t, [b'123', b'45', b'6', b'78', b'90'])
        bp = encode(s)
        self.assertEqual(bp, b'\0\0\x02\0'
                             b'\0\0\0\x03' b'bye\0'
                             b'\0\0\0\x03' b'123\0'
                             b'\0\0\0\x02' b'45\0\0'
                             b'\0\0\0\x01' b'6\0\0\0'
                             b'\0\0\0\x02' b'78\0\0'
                             b'\0\0\0\x02' b'90\0\0'
                         )
        self.assertEqual(decode(self.SimpleStructure, bp), s)
          
    def test_optional_struct(self):
        myStruct = Structure.typedef('myStruct',
                                     ('n', Int32),
                                     ('s', String.typedef('s', 5)),
                                     ('t', FixedArray.typedef('t', size=5,
                                                              type=VarBytes.typedef('', 3))))
 
        optStruct = Optional(myStruct)
        yes = optStruct(1, b'hallo', (b'a', b'bc', b'def', b'gh', b''))
        no = optStruct(None)
        self.assertIsInstance(yes, myStruct)
        self.assertEqual(no, None)
         
        b_yes = encode(yes)
        b_no = encode(no)
        self.assertEqual(b_yes, b'\0\0\0\x01'
                                b'\0\0\0\x01'
                                b'\0\0\0\x05' b'hallo\0\0\0'
                                b'\0\0\0\x01' b'a\0\0\0'
                                b'\0\0\0\x02' b'bc\0\0'
                                b'\0\0\0\x03' b'def\0'
                                b'\0\0\0\x02' b'gh\0\0'
                                b'\0\0\0\0')
        self.assertEqual(b_no, b'\0\0\0\0')
        self.assertEqual(decode(optStruct, b_no), no)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()