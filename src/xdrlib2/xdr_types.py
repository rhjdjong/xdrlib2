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

class Float64(float):
    def encode(self):
        return struct.pack('>d', self)

class Float128(float):
    def encode(self):
        signbit = 1 if math.copysign(1, self) < 0 else 0
        if self == 0.0:
            exponent = 0
            fraction = 0
        else:
            m, p = math.frexp(self)
            m = abs(m)
            fraction = round((2*m - 1) * 2**112)
            exponent = p + 16382
        number = (signbit << 127) | (exponent << 112) | fraction
        return number.to_bytes(16, 'big')

