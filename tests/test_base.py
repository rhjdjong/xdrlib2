'''
Created on 28 dec. 2015

@author: Ruud
'''
import unittest

from xdrlib2 import block_size, endian

class TestPackageStructure(unittest.TestCase):
    def test_can_access_xdrlib2(self):
        self.assertIsInstance(block_size, int)
        self.assertIsInstance(endian, str)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
