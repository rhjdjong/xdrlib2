'''
Created on 28 dec. 2015

@author: Ruud
'''
import unittest
import math

from xdrlib2 import *

class TestPackageStructure(unittest.TestCase):

    def test_can_access_xdrlib2(self):
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
            x = Int32(v)
            self.assertEqual(x, v)
            self.assertIsInstance(x, int)
            self.assertEqual(pack(x), p)
            self.assertEqual(x, unpack(Int32, p))
    
    def test_invalid_integer_values(self):
        for v in [0x80000000, 0x1234567890, -0x80000001, -0x1234567890]:
            with self.assertRaises(ValueError):
                Int32(v)

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
            x = Int32u(v)
            self.assertEqual(x, v)
            self.assertIsInstance(x, int)
            self.assertEqual(pack(x), p)
            self.assertEqual(x, unpack(Int32u, p))
    
    def test_invalid_unsigned_integer_values(self):
        for v in [0x100000000, 0x1234567890, -1,  -0x1234567890]:
            with self.assertRaises(ValueError):
                Int32u(v)

            
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
            x = Int64(v)
            self.assertEqual(x, v)
            self.assertIsInstance(x, int)
            self.assertEqual(pack(x), p)
            self.assertEqual(x, unpack(Int64, p))
    
    def test_invalid_hyper_integer_values(self):
        for v in [0x8000000000000000, 0x1234567890abcdef12345, -0x8000000000000001, -0x1234567890abcdef12345]:
            with self.assertRaises(ValueError):
                Int64(v)

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
            x = Int64u(v)
            self.assertEqual(x, v)
            self.assertIsInstance(x, int)
            self.assertEqual(pack(x), p)
            self.assertEqual(x, unpack(Int64u, p))
    
    def test_invalid_unsigned_hyper_integer_values(self):
        for v in [0x10000000000000000, 0x1234567890abcdef12345, -1,  -0x1234567890abcdef12345]:
            with self.assertRaises(ValueError):
                Int64u(v)

    def test_integer_class_construction(self):
        my_int32 = Int32Type('my_int32')
        my_int32u = Int32uType('my_int32u')
        my_int64 = Int64Type('my_int64')
        my_int64u = Int64uType('my_int64u')
        self.assertTrue(issubclass(my_int32, Int32))
        self.assertTrue(issubclass(my_int32u, Int32u))
        self.assertTrue(issubclass(my_int64, Int64))
        self.assertTrue(issubclass(my_int64u, Int64u))


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
                
            x = Float32(v)
            self.assertEqual(x, v)
            self.assertIsInstance(x, float)
            self.assertEqual(pack(x), bp)
            self.assertEqual(x, unpack(Float32, bp))
        
    def test_special_values_float32(self):
        inf = float('inf')
        x = Float32(inf)
        self.assertTrue(math.isinf(x))
        self.assertIsInstance(x, float)

        pv = 255<<23
        bp = pv.to_bytes(4, 'big')
        self.assertEqual(pack(x), bp)
        self.assertTrue(math.isinf(unpack(Float32, bp)))
        
        x = Float32(-inf)
        pv = 1<<31 | 255<<23
        bp = pv.to_bytes(4, 'big')
        self.assertEqual(pack(x), bp)
        self.assertTrue(math.isinf(unpack(Float32, bp)))
        self.assertLess(unpack(Float32, bp), 0)
        
        nan = float('nan')
        x = Float32(nan)
        self.assertTrue(math.isnan(x))
        self.assertIsInstance(x, float)
        packed_nan = pack(x)
        pv = int.from_bytes(packed_nan, 'big')
        e = (pv >> 23) & ((1<<8) - 1)
        f = pv & ((1<<23) - 1)
        self.assertEqual(e, 255)
        self.assertNotEqual(f & (1<<22), 0) # Quiet NaN has first bit of fraction set
        self.assertTrue(math.isnan(unpack(Float32, packed_nan)))
        
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
            self.assertTrue(math.isnan(unpack(Float32, packed)))
                
            
    def test_regular_float64(self):
        # Construct the packed byte values from first principles
        # Bit 63: sign bit
        # Bit 52-62: exponent, biased by 1023
        # Bit 0-51: fractional part of the numbers mantissa (leading 1. is implied).
        for v in (0.0, -0.0, 0.75, -10.375):
            pv = 1<<63 if math.copysign(1, v) < 0 else 0 # regular check for <0 looses the sign of -0.0
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
                
            x = Float64(v)
            self.assertEqual(x, v)
            self.assertIsInstance(x, float)
            self.assertEqual(pack(x), bp)
            self.assertEqual(x, unpack(Float64, bp))

    def test_special_values_float64(self):
        inf = float('inf')
        x = Float64(inf)
        self.assertTrue(math.isinf(x))
        self.assertIsInstance(x, float)
        pv = 2047<<52
        bp = pv.to_bytes(8, 'big')
        self.assertEqual(pack(x), bp)
        self.assertTrue(math.isinf(unpack(Float64, bp)))
        
        x = Float64(-inf)
        pv = 1<<63 | 2047<<52
        bp = pv.to_bytes(8, 'big')
        self.assertEqual(pack(x), bp)
        self.assertTrue(math.isinf(unpack(Float64, bp)))
        self.assertLess(unpack(Float64, bp), 0)
        
        nan = float('nan')
        x = Float64(nan)
        self.assertTrue(math.isnan(x))
        packed_nan = pack(x)
        pv = int.from_bytes(packed_nan, 'big')
        e = (pv >> 52) & ((1<<11) - 1)
        f = pv & ((1<<52) - 1)
        self.assertEqual(e, 2047)
        self.assertNotEqual(f & (1<<51), 0) # Quiet NaN has first bit of fraction set
        self.assertTrue(math.isnan(unpack(Float64, packed_nan)))
        
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
            self.assertTrue(math.isnan(unpack(Float64, packed)))
                
    def test_float_class_construction(self):
        my_float32 = Float32Type('my_float32')
        my_float64 = Float64Type('my_flaot64')
        self.assertTrue(issubclass(my_float32, Float32))
        self.assertTrue(issubclass(my_float64, Float64))
    


class TestEnumeration(unittest.TestCase):
    class Colors(Enumeration):
        RED=2
        YELLOW=3
        BLUE=5
        
    def test_enum_values(self):
        self.assertIsInstance(self.Colors.RED, int)
        self.assertEqual(self.Colors.RED, 2)
        self.assertEqual(self.Colors.YELLOW, 3)
        self.assertEqual(self.Colors.BLUE, 5)
    
    def test_enum_packing(self):
        bp = pack(self.Colors.RED)
        self.assertEqual(bp, b'\0\0\0\x02')
        bp = pack(self.Colors.YELLOW)
        self.assertEqual(bp, b'\0\0\0\x03')
        bp = pack(self.Colors.BLUE)
        self.assertEqual(bp, b'\0\0\0\x05')
    
    def test_enum_construction(self):
        self.assertEqual(self.Colors(self.Colors.RED), self.Colors.RED)
        self.assertEqual(self.Colors(self.Colors.YELLOW), 3)
        self.assertEqual(self.Colors(5), self.Colors.BLUE)
        self.assertRaises(ValueError, self.Colors, 10)
    
    def test_enum_class_construction(self):
        my_enum = EnumerationType('my_enum', a=1, b=2, c=3)
        self.assertTrue(issubclass(my_enum, Enumeration))
        self.assertIn(Enumeration, my_enum.__mro__)
        self.assertEqual(my_enum(1), my_enum.a)
        self.assertEqual(my_enum(my_enum.b), 2)
        self.assertEqual(pack(my_enum.c), b'\0\0\0\x03')
        self.assertEqual(unpack(my_enum, b'\0\0\0\x01'), my_enum.a)
    
    def test_enum_class_construction_with_possible_name_conflicts(self):
        my_enum = EnumerationType('my_enum', pack=1, parse=2, unpack=3)
        self.assertEqual(my_enum.pack, 1)
        self.assertEqual(my_enum(2), my_enum.parse)
        self.assertEqual(my_enum(my_enum.unpack), 3)
        self.assertEqual(pack(my_enum.pack), b'\0\0\0\x01')
        self.assertEqual(pack(my_enum(1)), b'\0\0\0\x01')
        self.assertEqual(unpack(my_enum, b'\0\0\0\x03'), my_enum.unpack)
        
        
                    
class TestBoolean(unittest.TestCase):
    def test_boolean_values(self):
        self.assertIsInstance(FALSE, int)
        self.assertIsInstance(TRUE, int)
        self.assertEqual(FALSE, False)
        self.assertEqual(TRUE, True)
        self.assertEqual(FALSE, 0)
        self.assertEqual(TRUE, 1)
        self.assertTrue(TRUE)
        self.assertFalse(FALSE)
    
    def test_boolean_packing(self):
        bp = pack(FALSE)
        self.assertEqual(bp, b'\0\0\0\0')
        self.assertEqual(unpack(Boolean, bp), FALSE)
        
        bp = pack(TRUE)
        self.assertEqual(bp, b'\0\0\0\x01')
        self.assertEqual(unpack(Boolean, bp), TRUE)
    
    def test_boolean_construction(self):
        self.assertEqual(Boolean(True), TRUE)
        self.assertEqual(Boolean(False), FALSE)
        self.assertEqual(Boolean(0), FALSE)
        self.assertEqual(Boolean(1), TRUE)
        self.assertRaises(ValueError, Boolean, 2)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
