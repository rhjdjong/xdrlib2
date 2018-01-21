# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import struct
import math

class _Bounded(int):
    def __new__(cls, value=0):
        v = super().__new__(cls, value)
        if cls.min <= v < cls.max:
            return v
        raise ValueError(f"Value {value!r} is out of range for class {cls.__name__}")

    def encode(self):
        return struct.pack(self.fmt, self)

    @classmethod
    def decode(cls, packed):
        v = struct.unpack(cls.fmt, packed)[0]
        return cls(v)


class Int32(_Bounded):
    min = -2**31
    max = 2**31
    fmt = '>i'


class Int32u(_Bounded):
    min = 0
    max = 2**32
    fmt = '>I'


class Int64(_Bounded):
    min = -2**63
    max = 2**63
    fmt = '>q'


class Int64u(_Bounded):
    min = 0
    max = 2**64
    fmt = '>Q'


class Float32(float):
    def encode(self):
        return struct.pack('>f', self)

    @classmethod
    def decode(cls, packed):
        value = struct.unpack('>f', packed)[0]
        return cls(value)

class Float64(float):
    def encode(self):
        return struct.pack('>d', self)

    @classmethod
    def decode(cls, packed):
        value = struct.unpack('>d', packed)[0]
        return cls(value)


class Float128(float):
    def encode(self):
        signbit = 1 if math.copysign(1, self) < 0 else 0
        if math.isinf(self):
            exponent = 32767
            fraction = 0
        elif math.isnan(self):
            exponent = 32767
            packed_double = struct.pack('>d', self)
            fraction = packed_double & ((1<<52) - 1)
            fraction <<= 60
        elif self == 0.0:
            exponent = 0
            fraction = 0
        else:
            m, p = math.frexp(self)
            m = abs(m)
            fraction = round((2*m - 1) * 2**112)
            exponent = p + 16382
        number = (signbit << 127) | (exponent << 112) | fraction
        return number.to_bytes(16, 'big')

    @classmethod
    def decode(cls, packed):
        number = int.from_bytes(packed, 'big')
        fraction = number & ((1<<112) - 1)
        number >>= 112
        exponent = number & ((1<<15) - 1)
        number >>= 15
        signbit = number & 1

        if exponent == 32765 and fraction != 0:
            float_exponent = 2047
            float_fraction = fraction >> 60
            if float_fraction == 0:
                float_fraction |= 1
            float_number = (signbit << 63) | (float_exponent << 52) | float_fraction
            packed_float = float_number.to_bytes(8, 'big')
            value = struct.unpack('>d', packed_float)[0]
        if exponent > 17406:
            value = float('inf') if signbit == 0 else float('-inf')
        elif exponent < 15361:
            value = (1 - 2*signbit) * fraction * 2**(-1022-112)
        else:
            value = (1 - 2*signbit) * (1 + fraction * 2**-112) * 2**(exponent-16383)
        return cls(value)

