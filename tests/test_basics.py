'''
Created on 28 dec. 2015

@author: Ruud
'''
import unittest
import math

import xdrlib2

class TestPackageStructure(unittest.TestCase):

    def test_can_access_xdrlib2(self):
        block_size = xdrlib2.block_size
        endian = xdrlib2.endian
        self.assertIsInstance(block_size, int)
        self.assertIsInstance(endian, str)

class TestIntegers(unittest.TestCase):
    
    def test_valid_integer_values(self):
        values = [(0, b'\0\0\0\0'),
                  (1, b'\0\0\0\1'),
                  (-1, b'\xff\xff\xff\xff'),
                  (0x7fffffff, b'\x7f\xff\xff\xff'),
                  (-0x80000000, b'\x80\0\0\0'),
                  (0x12345678, b'\x12\x34\x56\x78'),
                  (-0x12345678, b'\xed\xcb\xa9\x88' ),
                  ]
        for v, p in values:
            x = xdrlib2.int32(v)
            self.assertEqual(x.pack(), p)
            self.assertEqual(x, xdrlib2.int32.unpack(p))
    
    def test_invalid_integer_values(self):
        for v in [0x80000000, 0x1234567890, -0x80000001, -0x1234567890]:
            with self.assertRaises(ValueError):
                xdrlib2.int32(v)

    def test_valid_unsigned_integer_values(self):
        values = [(0, b'\0\0\0\0'),
                  (1, b'\0\0\0\1'),
                  (0x7fffffff, b'\x7f\xff\xff\xff'),
                  (0x80000000, b'\x80\0\0\0'),
                  (0xffffffff, b'\xff\xff\xff\xff'),
                  (0x12345678, b'\x12\x34\x56\x78'),
                  (0x98765432, b'\x98\x76\x54\x32'),
                  ]
        for v, p in values:
            x = xdrlib2.uint32(v)
            self.assertEqual(x.pack(), p)
            self.assertEqual(x, xdrlib2.uint32.unpack(p))
    
    def test_invalid_unsigned_integer_values(self):
        for v in [0x100000000, 0x1234567890, -1,  -0x1234567890]:
            with self.assertRaises(ValueError):
                xdrlib2.uint32(v)

            
    def test_valid_hyper_integer_values(self):
        values = [(0, b'\0\0\0\0\0\0\0\0'),
                  (1, b'\0\0\0\0\0\0\0\1'),
                  (-1, b'\xff\xff\xff\xff\xff\xff\xff\xff'),
                  (0x7fffffffffffffff, b'\x7f\xff\xff\xff\xff\xff\xff\xff'),
                  (-0x8000000000000000, b'\x80\0\0\0\0\0\0\0'),
                  (0x123456789abcdef0, b'\x12\x34\x56\x78\x9a\xbc\xde\xf0'),
                  (-0x123456789abcdef0, b'\xed\xcb\xa9\x87\x65\x43\x21\x10'),
                  ]
        for v, p in values:
            x = xdrlib2.int64(v)
            self.assertEqual(x.pack(), p)
            self.assertEqual(x, xdrlib2.int64.unpack(p))
    
    def test_invalid_hyper_integer_values(self):
        for v in [0x8000000000000000, 0x1234567890abcdef12345, -0x8000000000000001, -0x1234567890abcdef12345]:
            with self.assertRaises(ValueError):
                xdrlib2.int64(v)

    def test_valid_unsigned_hyper_integer_values(self):
        values = [(0, b'\0\0\0\0\0\0\0\0'),
                  (1, b'\0\0\0\0\0\0\0\1'),
                  (0x7fffffffffffffff, b'\x7f\xff\xff\xff\xff\xff\xff\xff'),
                  (0x8000000000000000, b'\x80\0\0\0\0\0\0\0'),
                  (0xffffffffffffffff, b'\xff\xff\xff\xff\xff\xff\xff\xff'),
                  (0x123456789abcdef0, b'\x12\x34\x56\x78\x9a\xbc\xde\xf0'),
                  (0xfedcba9876543210, b'\xfe\xdc\xba\x98\x76\x54\x32\x10'),
                  ]
        for v, p in values:
            x = xdrlib2.uint64(v)
            self.assertEqual(x.pack(), p)
            self.assertEqual(x, xdrlib2.uint64.unpack(p))
    
    def test_invalid_unsigned_hyper_integer_values(self):
        for v in [0x10000000000000000, 0x1234567890abcdef12345, -1,  -0x1234567890abcdef12345]:
            with self.assertRaises(ValueError):
                xdrlib2.uint64(v)


class TestFloats(unittest.TestCase):
    def test_regular_float32(self):
        # Construct the packed byte values from first principles
        # Bit 31: sign bit
        # Bit 23-30: exponent, biased by 127
        # Bit 0-22: fractional part of the numbers mantissa (leading 1. is implied).
        for v in (0.0, -0.0, 0.75, -10.375):
            pv = 1<<31 if math.copysign(1, v) < 0 else 0
            m, e = math.frexp(abs(v))
            # math.frexp returns mantissa and exponent (m and e) such that
            # 0.5 <= m < 1.
            # The fractional part in the packed value assumes an implied 1.,
            # in other words 1 <= m < 2.
            m *= 2
            e -= 1
            
            # Check for 0
            if m != 0:
                # Put the exponent in bits 23-30, biased by 127
                pv |= (e+127) << 23
                
                # Take the fractional part of the mantissa
                f = m - 1
                
                # Put the bits corresponding to the fractional part on the right position
                for p in reversed(range(23)):
                    f, b = math.modf(2*f)
                    pv |= int(b) << p
                
            bp = pv.to_bytes(4, 'big')
                
            x = xdrlib2.float32(v)
            self.assertEqual(x.pack(), bp)
            self.assertEqual(x, xdrlib2.float32.unpack(bp))
        
    def test_special_values_float32(self):
        inf = float('inf')
        x = xdrlib2.float32(inf)
        pv = 255<<23
        bp = pv.to_bytes(4, 'big')
        self.assertEqual(x.pack(), bp)
        self.assertTrue(math.isinf(xdrlib2.float32.unpack(bp)))
        
        x = xdrlib2.float32(-inf)
        pv = 1<<31 | 255<<23
        bp = pv.to_bytes(4, 'big')
        self.assertEqual(x.pack(), bp)
        self.assertTrue(math.isinf(xdrlib2.float32.unpack(bp)))
        self.assertLess(xdrlib2.float32.unpack(bp), 0)
        
        nan = float('nan')
        x = xdrlib2.float32(nan)
        packed_nan = x.pack()
        pv = int.from_bytes(packed_nan, 'big')
        e = (pv >> 23) & ((1<<8) - 1)
        f = pv & ((1<<23) - 1)
        self.assertEqual(e, 255)
        self.assertNotEqual(f & (1<<22), 0) # Quiet NaN has first bit of fraction set
        self.assertTrue(math.isnan(xdrlib2.float32.unpack(packed_nan)))
        
        # Try variations of the NaN bit formats
        p_list = [
                  pv | 1<<31,
                  pv | 1<<16,
                  pv | 1<<31 | 1<<16,
                  pv ^ 1<<22 | 1<<16,
                  pv | 1<<31 ^ 1<<22 | 1<<16,
                  ]
        for p in p_list:
            packed = p.to_bytes(4, 'big')
            self.assertTrue(math.isnan(xdrlib2.float32.unpack(packed)))
                
            
    def test_regular_float64(self):
        # Construct the packed byte values from first principles
        # Bit 63: sign bit
        # Bit 52-62: exponent, biased by 1023
        # Bit 0-51: fractional part of the numbers mantissa (leading 1. is implied).
        for v in (0.0, -0.0, 0.75, -10.375):
            pv = 1<<63 if math.copysign(1, v) < 0 else 0
            m, e = math.frexp(abs(v))
            # math.frexp returns mantissa and exponent (m and e) such that
            # 0.5 <= m < 1.
            # The fractional part in the packed value assumes an implied 1.,
            # in other words 1 <= m < 2.
            m *= 2
            e -= 1
            
            # Check for 0
            if m != 0:
                # Put the exponent in bits 52-62, biased by 1023
                pv |= (e+1023) << 52
                
                # Take the fractional part of the mantissa
                f = m - 1
                
                # Put the bits corresponding to the fractional part on the right position
                for p in reversed(range(52)):
                    f, b = math.modf(2*f)
                    pv |= int(b) << p
                
            bp = pv.to_bytes(8, 'big')
                
            x = xdrlib2.float64(v)
            self.assertEqual(x.pack(), bp)
            self.assertEqual(x, xdrlib2.float64.unpack(bp))

    def test_special_values_float64(self):
        inf = float('inf')
        x = xdrlib2.float64(inf)
        pv = 2047<<52
        bp = pv.to_bytes(8, 'big')
        self.assertEqual(x.pack(), bp)
        self.assertTrue(math.isinf(xdrlib2.float64.unpack(bp)))
        
        x = xdrlib2.float64(-inf)
        pv = 1<<63 | 2047<<52
        bp = pv.to_bytes(8, 'big')
        self.assertEqual(x.pack(), bp)
        self.assertTrue(math.isinf(xdrlib2.float64.unpack(bp)))
        self.assertLess(xdrlib2.float64.unpack(bp), 0)
        
        nan = float('nan')
        x = xdrlib2.float64(nan)
        packed_nan = x.pack()
        pv = int.from_bytes(packed_nan, 'big')
        e = (pv >> 52) & ((1<<11) - 1)
        f = pv & ((1<<52) - 1)
        self.assertEqual(e, 2047)
        self.assertNotEqual(f & (1<<51), 0) # Quiet NaN has first bit of fraction set
        self.assertTrue(math.isnan(xdrlib2.float64.unpack(packed_nan)))
        
        # Try variations of the NaN bit formats
        p_list = [
                  pv | 1<<63,
                  pv | 1<<16,
                  pv | 1<<63 | 1<<16,
                  pv ^ 1<<51 | 1<<16,
                  pv | 1<<63 ^ 1<<51 | 1<<16,
                  ]
        for p in p_list:
            packed = p.to_bytes(8, 'big')
            self.assertTrue(math.isnan(xdrlib2.float64.unpack(packed)))
                
            
            
    
            
            
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
