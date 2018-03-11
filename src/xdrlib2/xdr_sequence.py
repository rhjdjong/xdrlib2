# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import numbers

from .xdr_core import XdrType
from .xdr_integer import UnsignedInteger


class XdrSequence(XdrType):
    _variable = None

    @classmethod
    def _init_concrete_subclass(cls, **kwargs):
        return True, kwargs

    @classmethod
    def _verify_size(cls, size):
        return cls.minsize() <= size <= cls.size()

    def enocde_items(self):
        raise NotImplementedError(f"concrete XDR sequence type '{self.__class__.__name__:s}' "
                                  f"must implement method 'encode_items'")

    @classmethod
    def parse_items(self, itemcount):
        raise NotImplementedError(f"concrete XDR sequence type '{self.__class__.__name__:s}' "
                                  f"must implement classmethod 'parse_items'")

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
            itemcount = cls.size()
        return cls.parse_items(bstr, itemcount)

    @classmethod
    def size(cls):
        return cls._size

    @classmethod
    def minsize(cls):
        return 0 if cls._variable else cls.size()

    def __iadd__(self, other):
        self[:] = self + other
        return self

    def __imul__(self, other):
        self[:] = self * other
        return self

    def append(self, value):
        if not self._verify_size(len(self) + 1):
            raise ValueError(f"append operation leads to invalid length for '{self.__class__.__name__:s}' type")
        super().append(value)

    def extend(self, value):
        if not self._verify_size(len(self) + len(value)):
            raise ValueError(f"extend operation leads to invalid length for '{self.__class__.__name__:s}' type")
        super().extend(value)

    def clear(self):
        del self[:]

    def insert(self, pos, value):
        self[pos:pos] = value

    def remove(self, value):
        if not self._variable:
            raise ValueError(f"item removal leads to invalid length for '{self.__class__.__name__:s}' type")
        super().remove(value)

    def pop(self, pos=-1):
        if not self._variable:
            raise ValueError(f"pop operation leads to invalid length for '{self.__class__.__name__:s}' type")
        return super().pop(pos)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            removed_size = len(self[key])
            if not self._verify_size(len(self) - removed_size + len(value)):
                raise ValueError(f"item replacement leads to invalid length "
                                 f"for '{self.__class__.__name__:s}' type")
            for v in value:
                if not self._verify_element_type(v):
                    raise ValueError(f"invalid element type '{v.__class__.__name__:s}' "
                                     f"for '{self.__class__.__name__:s}' type")
        else:
            if not self._verify_element_type(value):
                raise ValueError(f"invalid element type '{value.__class__.__name__:s}' "
                                 f"for '{self.__class__.__name__:s}' type")
        super().__setitem__(key, value)

    def __delitem__(self, key):
        removed_size = len(self[key]) if isinstance(key, slice) else 1
        if not self._verify_size(len(self) - removed_size):
            raise ValueError(f"item deletion leads to invalid length "
                             f"for '{self.__class__.__name__:s}' type")
        super().__delitem__(key)


class XdrFixedSequence(XdrSequence):
    _variable = False


class XdrVarSequence(XdrSequence):
    _variable = True


class XdrOpaque(XdrSequence, bytearray):
    _parameter_names = ('size',)

    def __new__(cls, value=None):
        if not cls._final:
            raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")
        return super().__new__(cls, cls.minsize() if value is None else value)

    def __init__(self, value=None):
        if value is None:
            value = bytes(self.minsize())
        if not self._verify_size(len(value)):
            raise ValueError(f"invalid sequence length '{len(value):d}' "
                             f"for '{self.__class__.__name__:s}' instance")
        super().__init__(value)

    def _verify_element_type(self, value):
        return isinstance(value, int) and 0 <= value < 256

    def encode_items(self):
        return self + self.padding(len(self))

    @classmethod
    def parse_items(cls, bstr, size):
        padded_size = cls.padded_size(size)
        data = cls.remove_padding(bstr[:padded_size], size)
        return cls(data), bstr[padded_size:]


FixedOpaque = XdrOpaque.typedef('FixedOpaque', _variable=False)

VarOpaque = XdrOpaque.typedef('VarOpaque', _variable=True)

String = XdrOpaque.typedef('String', _variable=True)






