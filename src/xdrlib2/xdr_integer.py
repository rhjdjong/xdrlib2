# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import (
    XdrAtomic,
    XDR_BYTE_ORDER,
    _xdr_mode,
    xdr_padded,
    xdr_remove_padding,
)


class XdrInteger(XdrAtomic, int):
    _mode = _xdr_mode.ABSTRACT
    _parameters = ('min', 'max')
    _integer_parameters = {}

    @classmethod
    def _init_abstract_subclass_(cls, **kwargs):
        if kwargs:
            cls._integer_parameters = {}
            cls._integer_parameters.update(cls._integer_parameters)
            for name in cls._parameters:
                if name in kwargs:
                    if name in cls._integer_parameters:
                        raise TypeError(f"class '{cls.__name__:s}': redefinition of "
                                        f"class parameter '{name:s}' to {kwargs[name]!s}")
                    cls._integer_parameters[name] = int(kwargs.pop(name))
            if kwargs:
                raise TypeError(f"unexpected class parameter(s) {kwargs!s} for class '{cls.__name__:s}'")
            missing_parameters = set(cls._parameters) - set(cls._integer_parameters.keys())
            if missing_parameters:
                raise TypeError(f"missing class parameters {missing_parameters!s} "
                                f"for class '{cls.__name__:s}'")
            if cls.max <= cls.min:
                raise ValueError(f"{cls.__name__:s}: minimum value ({cls.min:d}) "
                                 f"must be less than maximum value ({cls.max:d})")
            cls._integer_parameters['signed'] = cls.min < 0
            size = (cls.max - cls.min).bit_length() - 1
            cls._packed_size = size // 8 + (1 if size % 8 else 0)
            cls._mode = _xdr_mode.FINAL

    @classmethod
    def _init_concrete_subclass(cls, **kwargs):
        pass

    def __new__(cls, value=None, **kwargs):
        if cls._mode is _xdr_mode.ABSTRACT:
            if value:
                raise NotImplementedError(f"Cannot instantiate abstract class {cls.__name__:s}'")
            return cls.typedef(**kwargs)
        else:  # Concrete class instantiation
            if value is None:
                value = 0
            v = super().__new__(cls, value, **kwargs)
            if cls.min <= v < cls.max:
                return v
            raise ValueError(f"Value {value!r} is out of range for class {cls.__name__}.\n"
                             f"\tAllowed range is {cls.min:d} <= value < {cls.max:d}.")

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls._integer_parameters[name]
        except KeyError:
            return super()._getattr_(name)

    def encode(self):
        bstr = self.to_bytes(self.packed_size, XDR_BYTE_ORDER, signed=self.signed)
        return xdr_padded(bstr)

    @classmethod
    def parse(cls, bstr):
        size = cls.packed_size
        v_str, bstr = xdr_remove_padding(bstr, size)
        v = int.from_bytes(v_str, XDR_BYTE_ORDER, signed=cls.signed)
        return cls(v), bstr

    def __repr__(self):
        return f'{self.__class__.__name__:s}({super().__repr__():s})'

    def __str__(self):
        return super().__str__()


Int32 = XdrInteger.typedef('Int32', min=-1<<31, max=1<<31)
Integer = Int32.typedef('Integer')


Int32u = XdrInteger.typedef('Int32u', min=0, max=1<<32)
UnsignedInteger = Int32u.typedef('UnsignedInteger')


Int64 = XdrInteger.typedef('Int64', min=-1<<63, max=1<<63)
Hyper = Int64.typedef('Hyper')


Int64u = XdrInteger.typedef('Int64u', min=0, max=1<<64)
UnsignedHyper = Int64u.typedef('UnsignedHyper')
