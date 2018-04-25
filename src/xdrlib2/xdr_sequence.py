# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType, xdr_mode, xdr_split_and_remove_padding, xdr_padded
from .xdr_integer import UnsignedInteger


class XdrSequence(XdrType):
    _mode = xdr_mode.ABSTRACT
    _parameters = ('variable',)
    _sequence_parameters = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if parameters:
            if cls._mode is xdr_mode.FINAL:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")

            existing_sequence_parameters = cls._sequence_parameters
            cls._sequence_parameters = {}
            cls._sequence_parameters.update(existing_sequence_parameters)
            extra_parameters = parameters.keys() - cls._parameters
            if extra_parameters:
                raise TypeError(f"unexpected class parameter(s) {extra_parameters!s} "
                                f"for class '{cls.__name__:s}'")
            redefined_parameters = parameters.keys() & cls._sequence_parameters.keys()
            if redefined_parameters:
                raise TypeError(f"class '{cls.__name__:s}': redefinition of "
                                f"class parameter(s) {redefined_parameters!s}")
            cls._sequence_parameters.update(parameters)
            missing_parameters = cls._parameters - cls._sequence_parameters.keys()
            if missing_parameters:
                return  # Incomplete class definition

            if cls.variable:
                minsize = 0
            else:
                minsize = cls.size
            cls._sequence_parameters['minsize'] = minsize
            cls._mode = xdr_mode.FINAL

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls._sequence_parameters[name]
        except KeyError:
            return super()._getattr_(name)

    def __getattr__(self, name):
        try:
            return getattr(self.__class__, name)
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__:s}' object "
                                 f"has no attribute '{name:s}'") from None

    def __copy__(self):
        return self.__class__(self)

    @classmethod
    def _verify_size(cls, size):
        return cls.minsize <= size <= cls.size

    def _encode_items(self):
        raise NotImplementedError(f"concrete XDR sequence type '{self.__class__.__name__:s}' "
                                  f"must implement method '_encode_items'")

    @classmethod
    def _decode_items(self, itemcount):
        raise NotImplementedError(f"concrete XDR sequence type '{self.__class__.__name__:s}' "
                                  f"must implement classmethod '_decode_items'")

    def _encode_(self):
        if self.variable:
            return UnsignedInteger(len(self))._encode_() + self._encode_items()
        else:
            return self._encode_items()

    @classmethod
    def _decode_(cls, bstr):
        if cls.variable:
            itemcount, bstr = UnsignedInteger._decode_(bstr)
        else:
            itemcount = cls.size
        return cls._decode_items(bstr, itemcount)

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
        if not self.variable:
            raise ValueError(f"item removal leads to invalid length for '{self.__class__.__name__:s}' type")
        super().remove(value)

    def pop(self, pos=-1):
        if not self.variable:
            raise ValueError(f"pop operation leads to invalid length for '{self.__class__.__name__:s}' type")
        return super().pop(pos)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            removed_size = len(self[key])
            if not self._verify_size(len(self) - removed_size + len(value)):
                raise ValueError(f"item replacement leads to invalid length "
                                 f"for '{self.__class__.__name__:s}' type")
            super().__setitem__(key, self._make_slice(value))
        else:
            super().__setitem__(key, self._make_item(value))

    def __delitem__(self, key):
        removed_size = len(self[key]) if isinstance(key, slice) else 1
        if not self._verify_size(len(self) - removed_size):
            raise ValueError(f"item deletion leads to invalid length "
                             f"for '{self.__class__.__name__:s}' type")
        super().__delitem__(key)

    def __repr__(self):
        return f"{self.__class__.__name__:s}(({', '.join(str(v) for v in self):s}))"


class XdrOpaque(XdrSequence, bytearray):
    _parameters = ('variable', 'size')

    def __init__(self, value=None):
        if self.__class__._mode is xdr_mode.ABSTRACT:
            raise NotImplementedError(f"cannot instantiate abstract '{self.__class__.__name__:s}' class")

        if value is None:
            value = bytes(self.minsize)
        if not self._verify_size(len(value)):
            raise ValueError(f"invalid sequence length '{len(value):d}' "
                             f"for '{self.__class__.__name__:s}' instance")
        super().__init__(value)

    def _make_item(self, value):
        if isinstance(value, int) and 0 <= value < 256:
            return value
        raise ValueError(f"invalid element {value!r} for object type '{self.__class__.__name__:s}'")

    def _make_slice(self, value):
        if all(isinstance(v, int) and 0 <= v < 256 for v in value):
            return value
        raise ValueError(f"invalid slice {value!r} for object type '{self.__class__.__name__:s}'")

    def _encode_items(self):
        return xdr_padded(self)

    @classmethod
    def _decode_items(cls, bstr, size):
        # padded_size = cls.padded_size(size)
        data, bstr = xdr_split_and_remove_padding(bstr, size)
        return cls(data), bstr


class XdrArray(XdrSequence, list):
    _parameters = ('variable', 'size', 'type')
    _array_parameters = {n: None for n in _parameters}

    def __init__(self, value=None):
        if self.__class__._mode is xdr_mode.ABSTRACT:
            raise NotImplementedError(f"cannot instantiate abstract '{self.__class__.__name__:s}' class")

        if value is None:
            lst = [self.type()] * self.minsize
        else:
            lst = [x if isinstance(x, self.type) else self.type(x) for x in value]
        if not self._verify_size(len(lst)):
            raise ValueError(f"invalid sequence length '{len(lst):d}' "
                             f"for '{self.__class__.__name__:s}' instance")
        super().__init__(lst)


    def _make_item(self, value):
        return self.type(value)

    def _make_slice(self, value):
        return (self.type(v) for v in value)

    def _encode_items(self):
        return b''.join(x._encode_() for x in self)

    @classmethod
    def _decode_items(cls, bstr, size):
        items = []
        for _ in range(size):
            item, bstr = cls.type._decode_(bstr)
            items.append(item)
        return cls(items), bstr


FixedOpaque = XdrOpaque.typedef('FixedOpaque', variable=False)

VarOpaque = XdrOpaque.typedef('VarOpaque', variable=True)

String = XdrOpaque.typedef('String', variable=True)

FixedArray = XdrArray.typedef('FixedArray', variable=False)

VarArray = XdrArray.typedef('VarArray', variable=True)






