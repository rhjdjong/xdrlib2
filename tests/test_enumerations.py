'''
Created on 31 aug. 2016

@author: Ruud
'''
import unittest

from xdrlib2 import *

class TestBaseEnumerations(unittest.TestCase):
    def test_base_enumeration_cannot_be_instantiated(self):
        self.assertRaises(NotImplementedError, Enumeration)


class TestDerivedEnumeration(unittest.TestCase):
    class MyEnum(Enumeration):
        RED = 2
        YELLOW = 3
        BLUE = 5
    
    FileKind = Enumeration.make('FileKind', TEXT=0, DATA=1, EXEC=2)
    
    def tearDown(self):
        glob = globals()
        for name in ('RED', 'YELLOW', 'BLUE', 'TEXT', 'DATA', 'EXEC'):
            try:
                del glob[name]
            except KeyError:
                pass
    
    def test_names_are_in_global_namespace(self):
        for name in ('RED', 'YELLOW', 'BLUE'):
            self.assertIn(name, globals())
        for name in ('TEXT', 'DATA', 'EXEC'):
            self.assertIn(name, globals())
    
    def test_enum_default_values(self):
        self.assertEqual(self.MyEnum(), 2)
        self.assertEqual(self.FileKind(), 0)
    
    
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()