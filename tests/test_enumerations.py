'''
Created on 31 aug. 2016

@author: Ruud
'''
import unittest

import xdrlib2
from xdrlib2 import *


class TestBaseEnumerations(unittest.TestCase):
    def test_base_enumeration_cannot_be_instantiated(self):
        self.assertRaises(NotImplementedError, Enumeration)


class TestDerivedEnumeration(unittest.TestCase):
    class MyEnum(Enumeration):
        RED = 2
        YELLOW = 3
        BLUE = 5
    
    FileKind = Enumeration.typedef('FileKind', TEXT=0, DATA=1, EXEC=2)
    
    def test_names_are_in_global_namespace(self):
        self.assertEqual(TEXT, 0) # @UndefinedVariable
        self.assertEqual(DATA, 1) # @UndefinedVariable
        self.assertEqual(EXEC, 2) # @UndefinedVariable
        self.assertEqual(RED, 2) # @UndefinedVariable
        self.assertEqual(YELLOW, 3) # @UndefinedVariable
        self.assertEqual(BLUE, 5) # @UndefinedVariable
        self.assertIsInstance(RED, self.MyEnum) # @UndefinedVariable
        self.assertIsInstance(DATA, self.FileKind) # @UndefinedVariable
    
    def test_enum_default_values(self):
        self.assertEqual(self.MyEnum(), 2)
        self.assertEqual(self.FileKind(), 0)
    
    def test_enum_does_not_accept_invalid_value(self):
        self.assertRaises(ValueError, self.MyEnum, 0)
        self.assertRaises(ValueError, self.FileKind, -1)
    
    def test_enum_class_can_be_instantiated_with_named_values(self):
        v = self.MyEnum(BLUE) # @UndefinedVariable
        self.assertEqual(v, 5)
        v = self.FileKind(EXEC) # @UndefinedVariable
        self.assertEqual(v, 2)

    def test_encoding_and_decoding(self):
        for v, p in ((RED, b'\0\0\0\x02'), # @UndefinedVariable
                     (YELLOW, b'\0\0\0\x03'), # @UndefinedVariable
                     (BLUE, b'\0\0\0\x05'), # @UndefinedVariable
                    ):
            self.assertEqual(encode(v), p)
            x = decode(self.MyEnum, p)
            self.assertIsInstance(x, self.MyEnum)
            self.assertEqual(x, v)
        for v, p in ((TEXT, b'\0\0\0\0'), # @UndefinedVariable
                     (DATA, b'\0\0\0\x01'), # @UndefinedVariable
                     (EXEC, b'\0\0\0\x02'), # @UndefinedVariable
                    ):
            self.assertEqual(encode(v), p)
            x = decode(self.FileKind, p)
            self.assertIsInstance(x, self.FileKind)
            self.assertEqual(x, v)
    
    def test_decoding_invalid_data_fails(self):
        self.assertRaises(ValueError, decode, self.MyEnum, b'\0\0\0\0')
        self.assertRaises(ValueError, decode, self.FileKind, b'\xff\xff\xff\xff')

class TestBoolean(unittest.TestCase):
    def test_boolean_values(self):
        self.assertEqual(xdrlib2.FALSE, 0) # @UndefinedVariable
        self.assertEqual(xdrlib2.TRUE, 1) # @UndefinedVariable
        self.assertIsInstance(xdrlib2.FALSE, Boolean) # @UndefinedVariable
        self.assertIsInstance(xdrlib2.TRUE, Enumeration) # @UndefinedVariable
        
            
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()