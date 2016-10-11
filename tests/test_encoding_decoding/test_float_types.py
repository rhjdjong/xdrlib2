'''
Created on 11 okt. 2016

@author: Ruud
'''
import unittest
import math

import xdrlib2 as xdr
from xdrlib2.xdr_base import byteorder
from xdrlib2.xdr_types import _pad_size as pad_size
from xdrlib2.xdr_types import _padding as padding


class TestFloatEncodingDecoding(unittest.TestCase):
    bin_data = {
        xdr.Float32: {'size': 4, 'e': 8, 'f': 23,},
        xdr.Float64: {'size': 8, 'e': 11, 'f': 52},
        xdr.Float128: {'size': 16, 'e': 15, 'f': 112}
        }
    
    def parse_binary_representation(self, cls, source):
        # Parse a floating-point binary representation
        # Returns the sign, exponent, and fractional part
        size = self.bin_data[cls]['size']
        e_size = self.bin_data[cls]['e']
        f_size = self.bin_data[cls]['f']
        self.assertEqual(len(source), size)
        
        if pad_size(size) > 0:
            source = source[:-pad_size(size)]
            
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
        return ((sign << (e_size + f_size)) | (exponent << f_size) | fraction).to_bytes(size, byteorder) + padding(size)
        
    def test_encoding_regular(self):
        floatvalues = {xdr.Float32: ((0.0, 0, 0, 0),
                                     (-1.0, 1, 127, 0),
                                     (1.5, 0, 127, 1<<22),
                                     (-0.1, 1, 123, 0x4ccccd)),
                       xdr.Float64: ((0.0, 0, 0, 0),
                                     (-1.0, 1, 1023, 0),
                                     (1.5, 0, 1023, 1<<51),
                                     (-0.1, 1, 1019, 0x999999999999a)),
                       xdr.Float128: ((0.0, 0, 0, 0),
                                      (-1.0, 1, 16383, 0),
                                      (1.5, 0, 16383, 1<<111),
                                      (-0.1, 1, 16379, 0x999999999999a<<60)),
                       }
        
        for float_type, values in floatvalues.items():
            for value, sign, exponent, fraction in values:
                with self.subTest(float_type=float_type, value=value):
                    b = float_type(value).encode()
                    s, e, f = self.parse_binary_representation(float_type, b)
                    self.assertEqual((s, e, f), (sign, exponent, fraction))
        
    def test_decoding_regular_exact(self):
        floatvalues = {xdr.Float32: ((0.0, 0, 0, 0),
                                     (-0.0, 1, 0, 0),
                                     (-1.0, 1, 127, 0),
                                     (1.5, 0, 127, 1<<22)),
                       xdr.Float64: ((0.0, 0, 0, 0),
                                     (-0.0, 1, 0, 0),
                                     (-1.0, 1, 1023, 0),
                                     (1.5, 0, 1023, 1<<51)),
                       xdr.Float128: ((0.0, 0, 0, 0),
                                      (-0.0, 1, 0, 0),
                                      (-1.0, 1, 16383, 0),
                                      (1.5, 0, 16383, 1<<111)),
                       }
        for float_type, values in floatvalues.items():
            for value, sign, exponent, fraction in values:
                with self.subTest(float_type=float_type, value=value):
                    b = self.make_binary_representation(float_type, sign, exponent, fraction)
                    x = float_type.decode(b)
                    self.assertIsInstance(x, float_type)
                    self.assertEqual(value, x)
    

    def test_decoding_regular_approximate(self):
        floatvalues = {xdr.Float32: (-0.1, 1, 123, 0x4ccccd, 2**-23),
                       xdr.Float64: (-0.1, 1, 1019, 0x999999999999a, 2**-52),
                       xdr.Float128: (-0.1, 1, 16379, 0x999999999999a<<60, 2**-52)}
        for float_type, (value, sign, exponent, fraction, eps) in floatvalues.items():
            with self.subTest(float_type=float_type, value=value):
                b = self.make_binary_representation(float_type, sign, exponent, fraction)
                x = float_type.decode(b)
                self.assertIsInstance(x, float_type)
                self.assertAlmostEqual(value, x, delta=abs(value*eps))


    def test_encoding_nan(self):
        nan_sign = {'nan': 0, '-nan': 1}
        nan_exponent = {xdr.Float32: 255, xdr.Float64: 2047, xdr.Float128: 32767}
        
        for nan, sign in nan_sign.items():
            for float_type, exponent in nan_exponent.items():
                with self.subTest(nan=nan, float_type=float_type):
                    b = float_type.encode(nan)
                    s, e, f = self.parse_binary_representation(float_type, b)
                    self.assertEqual((s, e), (sign, exponent))
                    self.assertNotEqual(f, 0)
        
    def test_encoding_inf(self):
        inf_sign = {'inf': 0, '-inf': 1}
        inf_exponent = {xdr.Float32: 255, xdr.Float64: 2047, xdr.Float128: 32767}

        for inf, sign in inf_sign.items():
            for float_type, exponent in inf_exponent.items():
                with self.subTest(inf=inf, float_type=float_type):
                    b = float_type.encode(inf)
                    s, e, f = self.parse_binary_representation(float_type, b)
                    self.assertEqual((s, e, f), (sign, exponent, 0))
    
    def test_decoding_nan(self):
        nan_sign = {'nan': 0, '-nan': 1}
        nan_exponent = {xdr.Float32: 255, xdr.Float64: 2047, xdr.Float128: 32767}
        
        for nan, sign in nan_sign.items():
            for float_type, exponent in nan_exponent.items():
                for offset in range(self.bin_data[float_type]['f']):
                    with self.subTest(nan=nan, float_type=float_type, offset=offset):
                        b = self.make_binary_representation(float_type, sign, exponent, 1<<offset) 
                        x = float_type.decode(b)
                        self.assertIsInstance(x, float_type)
                        self.assertTrue(math.isnan(x))

                   
    def test_decoding_inf(self):
        inf_sign = {'inf': 0, '-inf': 1}
        inf_exponent = {xdr.Float32: 255, xdr.Float64: 2047, xdr.Float128: 32767}

        for inf, sign in inf_sign.items():
            for float_type, exponent in inf_exponent.items():
                with self.subTest(inf=inf, float_type=float_type):
                    b = self.make_binary_representation(float_type, sign, exponent, 0) 
                    x = float_type.decode(b)
                    self.assertIsInstance(x, float_type)
                    self.assertTrue(math.isinf(x))
                    self.assertTrue(x < 0 if sign else x > 0)
            
    def test_encoding_subnormal(self):
        exponent_bias = {xdr.Float32: 127,
                         xdr.Float64: 1023,
                         xdr.Float128: 16383}
        for float_type in self.bin_data:
            mantissa_size = self.bin_data[float_type]['f']
            bias = exponent_bias[float_type]
           
            for i in range(mantissa_size):
                with self.subTest(float_type=float_type, i=i):
                    v = 0.5 * 2**(1-bias-i)
                    b = float_type(v).encode()
                    s, e, f = self.parse_binary_representation(float_type, b)
                    if float_type is xdr.Float128:
                        self.assertEqual((s, e, f), (0, 0, 0), 'Failed for i={}'.format(i))
                    else:
                        self.assertEqual((s, e, f), (0, 0, 1<<(mantissa_size-1-i)), 'Failed for i={}'.format(i))
    

    def test_decoding_subnormal(self):
        exponent_bias = {xdr.Float32: 127,
                         xdr.Float64: 1023,
                         xdr.Float128: 16383}
        for float_type in self.bin_data:
            mantissa_size = self.bin_data[float_type]['f']
            bias = exponent_bias[float_type]
            for i in range(mantissa_size):
                with self.subTest(float_type=float_type, i=i):
                    b = self.make_binary_representation(float_type, 1, 0, 1<<(mantissa_size-1-i))
                    x = float_type.decode(b)
                    self.assertIsInstance(x, float_type)
                    self.assertAlmostEqual(x, -0.5 * 2**(1-bias-i), delta=0.5*(2**(1-bias-mantissa_size)), msg='Failed for {} ({})'.format(i, b))
           


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()