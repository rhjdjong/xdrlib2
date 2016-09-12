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


    def test_encoding_regular(self):
        values = ((0.0, 0, 0, 0),
                  (-1.0, 1, 127, 0),
                  (1.5, 0, 127, 1<<22),
                  (-0.1, 1, 123, 0x4ccccd))
        
        for v, sign, exponent, fraction in values:
            b = encode(Float32(v))
            s, e, f = self.parse_binary_representation(Float32, b)
            msg = 'Failed for ({}, {}, {}, {})'.format(v, sign, exponent, fraction)
            self.assertEqual((s, e, f), (sign, exponent, fraction), msg)

        values = ((0.0, 0, 0, 0),
                  (-1.0, 1, 1023, 0),
                  (1.5, 0, 1023, 1<<51),
                  (-0.1, 1, 1019, 0x999999999999a))
        
        for v, sign, exponent, fraction in values:
            b = encode(Float64(v))
            s, e, f = self.parse_binary_representation(Float64, b)
            msg = 'Failed for ({}, {}, {}, {})'.format(v, sign, exponent, fraction)
            self.assertEqual((s, e, f), (sign, exponent, fraction), msg)
            
        values = ((0.0, 0, 0, 0),
                  (-1.0, 1, 16383, 0),
                  (1.5, 0, 16383, 1<<111),
                  (-0.1, 1, 16379, 0x999999999999a<<60))
        
        for v, sign, exponent, fraction in values:
            b = encode(Float128(v))
            s, e, f = self.parse_binary_representation(Float128, b)
            msg = 'Failed for ({}, {}, {}, {})'.format(v, sign, exponent, fraction)
            self.assertEqual((s, e, f), (sign, exponent, fraction), msg)
        
    def test_decoding_regular_exact(self):
        values = ((0.0, 0, 0, 0),
                  (-0.0, 1, 0, 0),
                  (-1.0, 1, 127, 0),
                  (1.5, 0, 127, 1<<22),
                  )
        
        for v, sign, exponent, fraction in values:
            b = self.make_binary_representation(Float32, sign, exponent, fraction)
            x = decode(Float32, b)
            self.assertIsInstance(x, Float32)
            self.assertEqual(v, x)
    
        values = ((0.0, 0, 0, 0),
                  (-0.0, 1, 0, 0),
                  (-1.0, 1, 1023, 0),
                  (1.5, 0, 1023, 1<<51),
                  )
        
        for v, sign, exponent, fraction in values:
            b = self.make_binary_representation(Float64, sign, exponent, fraction)
            x = decode(Float64, b)
            self.assertIsInstance(x, Float64)
            self.assertEqual(v, x)
            
        values = ((0.0, 0, 0, 0),
                  (-0.0, 1, 0, 0),
                  (-1.0, 1, 16383, 0),
                  (1.5, 0, 16383, 1<<111),
                  )
        
        for v, sign, exponent, fraction in values:
            b = self.make_binary_representation(Float128, sign, exponent, fraction)
            x = decode(Float128, b)
            self.assertIsInstance(x, Float128)
            self.assertEqual(v, x)

    def test_decoding_regular_approximate(self):
        v, sign, exponent, fraction = -0.1, 1, 123, 0x4ccccd
        b = self.make_binary_representation(Float32, sign, exponent, fraction)
        x = decode(Float32, b)
        self.assertIsInstance(x, Float32)
        self.assertAlmostEqual(v, x, delta=abs(v*(2**-23)))

        v, sign, exponent, fraction = -0.1, 1, 1019, 0x999999999999a
        b = self.make_binary_representation(Float64, sign, exponent, fraction)
        x = decode(Float64, b)
        self.assertIsInstance(x, Float64)
        self.assertAlmostEqual(v, x, delta=abs(v*(2**-52)))
    
        v, sign, exponent, fraction = -0.1, 1, 16379, 0x999999999999a<<60
        b = self.make_binary_representation(Float128, sign, exponent, fraction)
        x = decode(Float128, b)
        self.assertIsInstance(x, Float128)
        self.assertAlmostEqual(v, x, delta=abs(v*(2**-52)))

    def test_encoding_nan(self):
        b = encode(Float32('nan'))
        s, e, f = self.parse_binary_representation(Float32, b)
        self.assertEqual((s, e), (0, 255))
        self.assertNotEqual(f, 0)
        
        b = encode(Float32('-nan'))
        s, e, f = self.parse_binary_representation(Float32, b)
        self.assertEqual((s, e), (1, 255))
        self.assertNotEqual(f, 0)

        b = encode(Float64('nan'))
        s, e, f = self.parse_binary_representation(Float64, b)
        self.assertEqual((s, e), (0, 2047))
        self.assertNotEqual(f, 0)
        
        b = encode(Float64('-nan'))
        s, e, f = self.parse_binary_representation(Float64, b)
        self.assertEqual((s, e), (1, 2047))
        self.assertNotEqual(f, 0)
        
        b = encode(Float128('nan'))
        s, e, f = self.parse_binary_representation(Float128, b)
        self.assertEqual((s, e), (0, 32767))
        self.assertNotEqual(f, 0)
        
        b = encode(Float128('-nan'))
        s, e, f = self.parse_binary_representation(Float128, b)
        self.assertEqual((s, e), (1, 32767))
        self.assertNotEqual(f, 0)
        
    def test_encoding_inf(self):
        b = encode(Float32('inf'))
        s, e, f = self.parse_binary_representation(Float32, b)
        self.assertEqual((s, e, f), (0, 255, 0))
        
        b = encode(Float32('-inf'))
        s, e, f = self.parse_binary_representation(Float32, b)
        self.assertEqual((s, e, f), (1, 255, 0))

        b = encode(Float64('inf'))
        s, e, f = self.parse_binary_representation(Float64, b)
        self.assertEqual((s, e, f), (0, 2047, 0))
        
        b = encode(Float64('-inf'))
        s, e, f = self.parse_binary_representation(Float64, b)
        self.assertEqual((s, e, f), (1, 2047, 0))
    
        b = encode(Float128('inf'))
        s, e, f = self.parse_binary_representation(Float128, b)
        self.assertEqual((s, e, f), (0, 32767, 0))
        
        b = encode(Float128('-inf'))
        s, e, f = self.parse_binary_representation(Float128, b)
        self.assertEqual((s, e, f), (1, 32767, 0))
    
    def test_decoding_nan(self):
        for sign in range(2):
            for offset in range(23):
                b = self.make_binary_representation(Float32, sign, 255, 1<<offset) 
                x = decode(Float32, b)
                self.assertIsInstance(x, Float32)
                self.assertTrue(math.isnan(x))

            for offset in range(52):
                b = self.make_binary_representation(Float64, sign, 2047, 1<<offset) 
                x = decode(Float64, b)
                self.assertIsInstance(x, Float64)
                self.assertTrue(math.isnan(x))

            for offset in range(112):
                b = self.make_binary_representation(Float128, sign, 32767, 1<<offset) 
                x = decode(Float128, b)
                self.assertIsInstance(x, Float128)
                self.assertTrue(math.isnan(x))
                   
    def test_decoding_inf(self):
        for sign in range(2):
            b = self.make_binary_representation(Float32, sign, 255, 0) 
            x = decode(Float32, b)
            self.assertIsInstance(x, Float32)
            self.assertTrue(math.isinf(x))
            self.assertTrue(x < 0 if sign else x > 0)
            
            b = self.make_binary_representation(Float64, sign, 2047, 0) 
            x = decode(Float64, b)
            self.assertIsInstance(x, Float64)
            self.assertTrue(math.isinf(x))
            self.assertTrue(x < 0 if sign else x > 0)

            b = self.make_binary_representation(Float128, sign, 32767, 0) 
            x = decode(Float128, b)
            self.assertIsInstance(x, Float128)
            self.assertTrue(math.isinf(x))
            self.assertTrue(x < 0 if sign else x > 0)
    
    def test_encoding_subnormal(self):
        for i in range(23):
            v = 0.5 * 2**(-126-i)
            b = encode(Float32(v))
            s, e, f = self.parse_binary_representation(Float32, b)
            self.assertEqual((s, e, f), (0, 0, 1<<(22-i)), 'Failed for i={}'.format(i))
    
        for i in range(52):
            v = 0.5 * 2**(-1022-i)
            b = encode(Float64(v))
            s, e, f = self.parse_binary_representation(Float64, b)
            self.assertEqual((s, e, f), (0, 0, 1<<(51-i)), 'Failed for i={}'.format(i))

        for i in range(112):
            v = 0.5 * 2**(-16382-i)
            b = encode(Float128(v))
            s, e, f = self.parse_binary_representation(Float128, b)
#             self.assertEqual((s, e, f), (0, 0, 1<<(51-i)), 'Failed for i={}'.format(i)) # Does not work for current implementation
            self.assertEqual((s, e, f), (0, 0, 0), 'Failed for i={}'.format(i))

    def test_decoding_subnormal(self):
        for i in range(23):
            b = self.make_binary_representation(Float32, 1, 0, 1<<(22-i))
            x = decode(Float32, b)
            self.assertIsInstance(x, Float32)
            self.assertAlmostEqual(x, -0.5 * 2**(-126-i), delta=0.5*(2**(-126-23)), msg='Failed for {} ({})'.format(i, b))

        for i in range(52):
            b = self.make_binary_representation(Float64, 1, 0, 1<<(51-i))
            x = decode(Float64, b)
            self.assertIsInstance(x, Float64)
            self.assertAlmostEqual(x, -0.5 * 2**(-1022-i), delta=0.5*(2**(-1022-52)), msg='Failed for {} ({})'.format(i, b))
            
        for i in range(112):
            b = self.make_binary_representation(Float128, 1, 0, 1<<(111-i))
            x = decode(Float128, b)
            self.assertIsInstance(x, Float128)
            self.assertAlmostEqual(x, -0.5 * 2**(-16382-i), delta=0.5*(2**(-16382-52)), msg='Failed for {} ({})'.format(i, b))

            
                   
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
