# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrAtomic


class XdrInteger(XdrAtomic, int):
    _parameter_names = ('min', 'max')

    @classmethod
    def _init_concrete_subclass(cls, **kwargs):
        size = (cls.max() - cls.min()).bit_length() - 1
        cls._packed_size = size // 8 + (1 if size % 8 else 0)
        return True, kwargs

    def __new__(cls, value=0):
        v = super().__new__(cls, value)
        if cls.min() <= v < cls.max():
            return v
        raise ValueError(f"Value {value!r} is out of range for class {cls.__name__}.\n"
                         f"\tAllowed range is [{cls.min():d} .. {cls.max() - 1:d}].")

    def encode(self):
        return self.to_bytes(self.packed_size(), 'big', signed=self.signed())

    @classmethod
    def parse(cls, bstr):
        size = cls.packed_size()
        v = int.from_bytes(bstr[:size], 'big', signed=cls.signed())
        return cls(v), bstr[size:]

    def __repr__(self):
        return f'{self.__class__.__name__:s}({super().__repr__():s})'

    @classmethod
    def max(cls):
        return cls._max

    @classmethod
    def min(cls):
        return cls._min

    @classmethod
    def signed(cls):
        return cls.min() < 0


Int32 = XdrInteger.typedef('Int32', min=-1<<31, max=1<<31)
Integer = Int32


Int32u = XdrInteger.typedef('Int32u', min=0, max=1<<32)
UnsignedInteger = Int32u


Int64 = XdrInteger.typedef('Int64', min=-1<<63, max=1<<63)
Hyper = Int64


Int64u = XdrInteger.typedef('Int64u', min=0, max=1<<64)
UnsignedHyper = Int64u
