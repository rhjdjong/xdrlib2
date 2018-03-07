# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType
from .xdr_integer import UnsignedInteger

class XdrOpaque(XdrType, bytearray):
    _minsize = None
    _maxsize = None

    def __new__(cls, value=None):
        if value is None:
            value = b'\0' * cls._minsize
        if not cls._minsize <= len(value) <= cls._maxsize:
            raise ValueError(f"invalid sequence length '{len(value):d}' for '{cls.__name__:s}' instance")
        return super().__new__(cls, value)

    def __init__(self, value=None):
        if value is None:
            value = b'\0' * self._minsize
        super().__init__(value)

    @classmethod
    def size(cls):
        return cls._maxsize


class FixedOpaque(XdrOpaque):
    def __init_subclass__(cls, size=None):
        if cls._minsize is not None:
            raise TypeError(f"cannot subclass '{cls.__name__:s}' opaque type")
        cls._minsize = UnsignedInteger(size)
        cls._maxsize = UnsignedInteger(size)

    def encode(self):
        s = len(self)
        padding = b'\0' * ((s % 4) % 4)
        return self + padding

    @classmethod
    def decode(cls, bstr):
        return cls(bstr[:cls.size()])






