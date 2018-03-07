# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType


class XdrInteger(XdrType, int):
    _signed = None
    _min = None
    _max = None
    _packed_size = None

    def __init_subclass__(cls, size=0, signed=False, **kwargs):
        if cls._signed is None:
            cls._signed = signed
            if signed:
                cls._min = -(1 << (size - 1))
                cls._max = (1 << (size - 1))
            else:
                cls._min = 0
                cls._max = 1 << size
            cls._packed_size = size // 8 + (1 if size % 8 else 0)
        super().__init_subclass__()

    def __new__(cls, value=0):
        v = super().__new__(cls, value)
        if cls.min() <= v < cls.max():
            return v
        raise ValueError(f"Value {value!r} is out of range for class {cls.__name__}.\n"
                         f"\tAllowed range is [{cls.min():d} .. {cls.max() - 1:d}].")

    def encode(self):
        return self.to_bytes(self.size(), 'big', signed=self.signed())

    @classmethod
    def decode(cls, packed):
        v = int.from_bytes(packed, 'big', signed=cls.signed())
        return cls(v)

    def __repr__(self):
        return f'{self.__class__.__name__:s}({super().__repr__():s})'

    @classmethod
    def max(cls):
        return cls._max

    @classmethod
    def min(cls):
        return cls._min

    @classmethod
    def size(cls):
        return cls._packed_size

    @classmethod
    def signed(cls):
        return cls._signed


class Int32(XdrInteger, size=32, signed=True):
    pass


Integer = Int32


class Int32u(XdrInteger, size=32, signed=False):
    pass


UnsignedInteger = Int32u


class Int64(XdrInteger, size=64, signed=True):
    pass


Hyper = Int64


class Int64u(XdrInteger, size=64, signed=False):
    pass


UnsignedHyper = Int64u
