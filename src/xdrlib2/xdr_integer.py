# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrAtomic


class XdrInteger(XdrAtomic, int):
    _abstract = True
    _final = False

    _parameters = ('min', 'max')

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_creation_information(**kwargs)
        extra_names = set(parameters.keys()) - set(cls._parameters)
        if extra_names:
            raise TypeError(f"{cls.__name__:s}' subclass got unexpected parameter(s) {tuple(extra_names)!s}")
        if cls._abstract:
            if not all(parameters.get(n) is not None for n in cls._parameters):
                raise TypeError(f"incomplete instantiation of XdrInteger subclass '{cls.__name__:s}'")
            if parameters:
                cls._integer_min = int(parameters['min'])
                cls._integer_max = int(parameters['max'])
                if cls.max() <= cls.min():
                    raise ValueError(f"{cls.__name__:s}: minimum value ({cls.min():d}) "
                                     f"must be less than maximum value ({cls.max():d})")
                size = (cls.max() - cls.min()).bit_length() - 1
                cls._packed_size = size // 8 + (1 if size % 8 else 0)
                cls._abstract = False
                cls._final = True


    def __new__(cls, *args, **kwargs):
        if cls._abstract:  # Anonymous subclass creation
            return cls._create_anonymous_subclass(*args, **kwargs)
        else:  # Concrete class instantiation
            return cls._create_concrete_instance(*args, **kwargs)


    @classmethod
    def _create_concrete_instance(cls, value=None, **kwargs):
        if value is None:
            value = 0
        v = super().__new__(cls, value, **kwargs)
        if cls.min() <= v < cls.max():
            return v
        raise ValueError(f"Value {value!r} is out of range for class {cls.__name__}.\n"
                         f"\tAllowed range is {cls.min():d} <= value < {cls.max():d}.")


    def encode(self):
        bstr = self.to_bytes(self.packed_size(), 'big', signed=self.signed())
        return bstr + self.padding(len(bstr))

    @classmethod
    def parse(cls, bstr):
        size = cls.packed_size()
        padded_size = cls.padded_size(size)
        v_str = cls.remove_padding(bstr[:padded_size], size)
        v = int.from_bytes(v_str, 'big', signed=cls.signed())
        return cls(v), bstr[padded_size:]

    def __repr__(self):
        return f'{self.__class__.__name__:s}({super().__repr__():s})'

    def __str__(self):
        return super().__str__()

    @classmethod
    def max(cls):
        return cls._integer_max

    @classmethod
    def min(cls):
        return cls._integer_min

    @classmethod
    def signed(cls):
        return cls.min() < 0


Int32 = XdrInteger.typedef('Int32', min=-1<<31, max=1<<31)
Integer = Int32.typedef('Integer')


Int32u = XdrInteger.typedef('Int32u', min=0, max=1<<32)
UnsignedInteger = Int32u.typedef('UnsignedInteger')


Int64 = XdrInteger.typedef('Int64', min=-1<<63, max=1<<63)
Hyper = Int64.typedef('Hyper')


Int64u = XdrInteger.typedef('Int64u', min=0, max=1<<64)
UnsignedHyper = Int64u.typedef('UnsignedHyper')
