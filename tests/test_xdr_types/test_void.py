'''
Created on 9 okt. 2016

@author: Ruud
'''
import unittest

import xdrlib2 as xdr

class TestVoid(unittest.TestCase):
    def test_void_instantiation(self):
        v1 = xdr.Void()
        v2 = xdr.Void(None)
        self.assertEqual(v1, v2)
        self.assertEqual(v1, None)
    
    def test_void_encoding(self):
        v = xdr.Void()
        self.assertEqual(v.encode(), b'')
    
    def test_void_decoding(self):
        v = xdr.Void.decode(b'')
        self.assertIsInstance(v, xdr.Void)
        self.assertEqual(v, None)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()