'''
Created on 28 dec. 2015

@author: Ruud
'''
import unittest
import math

from xdrlib2 import *
from xdrlib2.xdr_types import _padding, _pad_size

class TestFloats(unittest.TestCase):
    bin_data = {
        Float32: {'size': 4, 'e': 8, 'f': 23},
        Float64: {'size': 8, 'e': 11, 'f': 52},
        Float128: {'size': 16, 'e': 15, 'f': 112}
        }
    
    def parse_binary_representation(self, cls, source):
        # Parse a floating-point binary representation
        # Returns the sign, exponent, and fractional part
        size = self.bin_data[cls]['size']
        e_size = self.bin_data[cls]['e']
        f_size = self.bin_data[cls]['f']
        self.assertEqual(len(source), size)
        
        if _pad_size(size) > 0:
            source = source[:-_pad_size(size)]
            
        number = int.from_bytes(source, byteorder)
        fraction = number & ((1<<f_size)-1)
        number >>= f_size
        exponent = number & ((1<<e_size)-1)
        number >>= e_size
        sign = number & 1
        
        return sign, exponent, fraction
    
    def make_binary_representation(self, cls, sign, exponent, fraction):
        size = self.bin_data[cls]['size']
        e_size = self.bin_data[cls]['e']
        f_size = self.bin_data[cls]['f']
        return ((sign << (e_size + f_size)) | (exponent << f_size) | fraction).to_bytes(size, byteorder) + _padding(size)
        
        
    def test_default_instantation(self):
        self.assertEqual(Float32(), 0.0)
        self.assertEqual(Float64(), 0.0)
        self.assertEqual(Float128(), 0.0)            



            
                   
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
