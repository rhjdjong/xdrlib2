'''
Created on 28 dec. 2015

@author: Ruud
'''
import unittest

from xdrlib2 import *

class TestPackageStructure(unittest.TestCase):
    def test_can_access_xdrlib2(self):
        self.assertIsInstance(block_size, int)
        self.assertIsInstance(endian, str)
        self.assertIsInstance(byteorder, str)


class TestVoid(unittest.TestCase):
    def test_void(self):
        v1 = Void()
        v2 = Void(None)
        self.assertEqual(v1, v2)
        self.assertEqual(v1, None)
          
        bp1 = encode(v1)
        bp2 = encode(v2)
        self.assertEqual(bp1, bp2)
        self.assertEqual(bp1, b'')
        self.assertEqual(decode(Void, bp1), v2)
          
    def test_optional_void(self):
        # This test is here for documentation purposes only.
        # The XDR specification syntax does not allow an optional void
        pass

class TestOptional(unittest.TestCase):
    def test_optional_is_idempotent(self):
        t = Optional(Int32)
        t_opt = Optional(t)
        self.assertIs(t, t_opt)

    def test_optional_class_name(self):
        t = Optional(Int32)
        self.assertEqual(t.__name__, '*Int32')
        self.assertTrue(issubclass(t, Int32))
    
    def test_cannot_create_optional_classes_through_derived_optional_class(self):
        opt_cls = Optional(Int32)
        self.assertRaises(TypeError, opt_cls, Float32)
    
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
