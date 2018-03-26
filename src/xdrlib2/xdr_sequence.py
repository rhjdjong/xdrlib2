# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import numbers

from .xdr_core import XdrType, _xdr_mode, xdr_remove_padding, xdr_padded
from .xdr_integer import UnsignedInteger


class XdrSequence(XdrType):
    _mode = _xdr_mode.ABSTRACT
    _parameters = ()
    _sequence_parameters = {}
    # def __new__(cls, *args, **kwargs):
    #     if cls._abstract:  # Anonymous subclass creation
    #         return cls._create_anonymous_subclass(*args, **kwargs)
    #     else:  # Concrete class instantiation
    #         return cls._create_concrete_instance(*args, **kwargs)


    # @classmethod
    # def _init_concrete_subclass(cls, **kwargs):
    #     return True, kwargs
    #
    @classmethod
    def _init_abstract_subclass_(cls, **kwargs):
        if kwargs:
            existing_sequence_parameters = cls._sequence_parameters
            cls._sequence_parameters = {}
            cls._sequence_parameters.update(existing_sequence_parameters)
            for name in cls._parameters:
                if name in kwargs:
                    if name in cls._sequence_parameters:
                        raise TypeError(f"class '{cls.__name__:s}': redefinition of "
                                        f"class parameter '{name:s}' to {kwargs[name]!s}")
                    cls._sequence_parameters[name] = kwargs.pop(name)
            if kwargs:
                raise TypeError(f"unexpected class parameter(s) {kwargs!s} for class '{cls.__name__:s}'")
            missing_parameters = set(cls._parameters) - set(cls._sequence_parameters.keys())
            if missing_parameters:
                return  # Incomplete class definition

            if cls.variable:
                minsize = 0
            else:
                minsize = cls.size
            cls._sequence_parameters['minsize'] = minsize
            cls._mode = _xdr_mode.FINAL

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

    @classmethod
    def _verify_size(cls, size):
        return cls.minsize <= size <= cls.size

    def enocde_items(self):
        raise NotImplementedError(f"concrete XDR sequence type '{self.__class__.__name__:s}' "
                                  f"must implement method 'encode_items'")

    @classmethod
    def parse_items(self, itemcount):
        raise NotImplementedError(f"concrete XDR sequence type '{self.__class__.__name__:s}' "
                                  f"must implement classmethod 'parse_items'")

    def encode(self):
        if self.variable:
            return UnsignedInteger(len(self)).encode() + self.encode_items()
        else:
            return self.encode_items()

    @classmethod
    def parse(cls, bstr):
        if cls.variable:
            itemcount, bstr = UnsignedInteger.parse(bstr)
        else:
            itemcount = cls.size
        return cls.parse_items(bstr, itemcount)

    # @classmethod
    # def size(cls):
    #     return cls._sequence_size
    #
    # @classmethod
    # def minsize(cls):
    #     return 0 if cls._sequence_variable else cls.size()
    #
    #
    # @classmethod
    # def type(cls):
    #     return cls._sequence_type

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

    # def __str__(self):
    #     return super().__str__()


class XdrOpaque(XdrSequence, bytearray):
    _parameters = ('variable', 'size')

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._mode is _xdr_mode.FINAL:
            if parameters:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
        if cls._mode is _xdr_mode.ABSTRACT:
            cls._init_abstract_subclass_(**parameters)
        else:
            cls._init_concrete_subclass_(**parameters)


    def __new__(cls, value=None, **kwargs):
        if cls._mode is _xdr_mode.ABSTRACT:  # Anonymous subclass creation
            if value is not None:
                raise NotImplementedError(f"Cannot instantiate abstract class {cls.__name__:s}'")
            return cls.typedef(**kwargs)
        else:  # Concrete class instantiation
            if value is None:
                value = bytes(cls.minsize)
            return super().__new__(cls, value, **kwargs)

    def __init__(self, value=None, **kwargs):
        if value is None:
            value = bytes(self.minsize)
        if not self._verify_size(len(value)):
            raise ValueError(f"invalid sequence length '{len(value):d}' "
                             f"for '{self.__class__.__name__:s}' instance")
        super().__init__(value, **kwargs)

    def _make_item(self, value):
        if isinstance(value, int) and 0 <= value < 256:
            return value
        raise ValueError(f"invalid element {value!r} for object type '{self.__class__.__name__:s}'")

    def _make_slice(self, value):
        if all(isinstance(v, int) and 0 <= v < 256 for v in value):
            return value
        raise ValueError(f"invalid slice {value!r} for object type '{self.__class__.__name__:s}'")

    def encode_items(self):
        return xdr_padded(self)

    @classmethod
    def parse_items(cls, bstr, size):
        # padded_size = cls.padded_size(size)
        data, bstr = xdr_remove_padding(bstr, size)
        return cls(data), bstr


class XdrArray(XdrSequence, list):
    _parameters = ('variable', 'size', 'type')
    _array_parameters = {n: None for n in _parameters}

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._mode is _xdr_mode.FINAL:
            if parameters:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
        if cls._mode is _xdr_mode.ABSTRACT:
            cls._init_abstract_subclass_(**parameters)
        else:
            cls._init_concrete_subclass_(**parameters)

    # def __init_subclass__(cls, **kwargs):
    #     parameters = cls._get_class_parameters(**kwargs)
    #     if cls._final:
    #         if parameters:
    #             raise TypeError(f"Cannot extend enumeration class '{cls.__name__:s}' "
    #                             f"with additional enumeration values {parameters!s}")
    #     else:
    #         extra_names = set(parameters.keys()) - set(cls._parameters)
    #         if extra_names:
    #             raise ValueError(f"{cls.__name__:s}' subclass got unexpected parameter(s) {tuple(extra_names)!s}")
    #         if cls._abstract:
    #             cls._array_parameters = cls._array_parameters.copy()
    #             for name, value in parameters.items():
    #                 cls._array_parameters[name] = value
    #                 if name == 'size':
    #                     if cls.variable:
    #                         minsize = 0
    #                     else:
    #                         minsize = value
    #                     cls._array_parameters['minsize'] = minsize
    #             for name in cls._parameters:
    #                 if getattr(cls, name) is None:
    #                     break
    #             else:
    #                 # Complete subclass
    #                 cls._abstract = False
    #                 cls._final = True

    # @classmethod
    # def _getattr_(cls, name):
    #     try:
    #         return cls._array_parameters[name]
    #     except KeyError:
    #         raise AttributeError(f"class '{cls.__name__:s}' "
    #                              f"has no attribute '{name:s}'") from None
    #

    # def __getattr__(self, name):
    #     try:
    #         return self.__class__._array_parameters[name]
    #     except KeyError:
    #         raise AttributeError(f"'{self.__class__.__name__:s}' object "
    #                              f"has no attribute '{name:s}'") from None
    #
    def __new__(cls, value=None, **kwargs):
        if cls._mode is _xdr_mode.ABSTRACT:  # Anonymous subclass creation
            if value is not None:
                raise NotImplementedError(f"Cannot instantiate abstract class {cls.__name__:s}'")
            return cls.typedef(**kwargs)
        else:  # Concrete class instantiation
            if value is None:
                value = [cls.type()] * cls.minsize
            return super().__new__(cls, value, **kwargs)

    # def __new__(cls, *args, **kwargs):
    #     if cls._abstract:  # Anonymous subclass creation
    #         return cls._create_anonymous_subclass(*args, **kwargs)
    #     else:  # Concrete class instantiation
    #         return cls._create_concrete_instance(*args, **kwargs)
    #
    # @classmethod
    # def _create_concrete_instance(cls, value=None, **kwargs):
    #     if value is None:
    #         value = [cls.type()] * cls.minsize
    #     return super().__new__(cls, value, **kwargs)
    #
    def __init__(self, value=None, **kwargs):
        if value is None:
            lst = [self.type()] * self.minsize
        else:
            lst = [self.type(x) for x in value]
        if not self._verify_size(len(lst)):
            raise ValueError(f"invalid sequence length '{len(lst):d}' "
                             f"for '{self.__class__.__name__:s}' instance")
        super().__init__(lst, **kwargs)


    def _make_item(self, value):
        return self.type(value)

    def _make_slice(self, value):
        return (self.type(v) for v in value)

    def encode_items(self):
        return b''.join(x.encode() for x in self)

    @classmethod
    def parse_items(cls, bstr, size):
        items = []
        for _ in range(size):
            item, bstr = cls.type.parse(bstr)
            items.append(item)
        return cls(items), bstr


FixedOpaque = XdrOpaque.typedef('FixedOpaque', variable=False)

VarOpaque = XdrOpaque.typedef('VarOpaque', variable=True)

String = XdrOpaque.typedef('String', variable=True)

FixedArray = XdrArray.typedef('FixedArray', variable=False)


class VarArray(XdrArray):
    variable = True






