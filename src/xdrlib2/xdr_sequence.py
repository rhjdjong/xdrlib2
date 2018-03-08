# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import numbers

from .xdr_core import XdrType
from .xdr_integer import UnsignedInteger


class XdrSequence(XdrType):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls._final and hasattr(cls, '_parameter_names') and \
                all(hasattr(cls, '_' + name) for name in cls._parameter_names):
            cls._final = True

    def encode(self):
        if self._variable:
            return UnsignedInteger(len(self)).encode() + self.encode_items()
        else:
            return self.encode_items()

    @classmethod
    def parse(cls, bstr):
        if cls._variable:
            itemcount, bstr = UnsignedInteger.parse(bstr)
        else:
            itemcount = cls.maxsize()
        return cls.parse_items(bstr, itemcount)

    @classmethod
    def maxsize(cls):
        return cls._maxsize

    @classmethod
    def minsize(cls):
        return 0 if cls._variable else cls.maxsize()


class XdrFixedSequence(XdrSequence):
    _variable = False


class XdrVarSequence(XdrSequence):
    _variable = True


class XdrOpaque(XdrSequence, bytearray):
    _parameter_names = ('maxsize',)

    def __new__(cls, value=None):
        if value is None:
            value = b'\0' * cls.minsize()
        if not cls.minsize() <= len(value) <= cls.maxsize():
            raise ValueError(f"invalid sequence length '{len(value):d}' for '{cls.__name__:s}' instance")
        return super().__new__(cls, value)

    def __init__(self, value=None):
        if value is None:
            value = b'\0' * self.minsize()
        super().__init__(value)

    def encode_items(self):
        return self + self.padding(len(self))

    @classmethod
    def parse_items(cls, bstr, size):
        padded_size = cls.padded_size(size)
        data = cls.remove_padding(bstr[:padded_size], size)
        return cls(data), bstr[padded_size:]


class FixedOpaque(XdrOpaque):
    _variable = False



class VarOpaque(XdrOpaque):
    _variable = True





