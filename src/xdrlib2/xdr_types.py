# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import struct


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
