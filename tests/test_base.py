'''
Created on 28 dec. 2015

@author: Ruud
'''
import unittest

import xdrlib2 as xdr

class TestPackageStructure(unittest.TestCase):
    def test_can_access_xdrlib2(self):
        self.assertIsInstance(xdr.block_size, int)
        self.assertIsInstance(xdr.endian, str)
        self.assertIsInstance(xdr.byteorder, str)


          

    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
