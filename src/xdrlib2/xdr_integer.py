# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import (
    XdrType,
    XDR_BYTE_ORDER,
    xdr_mode,
    xdr_padded,
    xdr_split_and_remove_padding,
)


class XdrInteger(XdrType, int):
    """
    :class:`XdrInteger` is the abstract base type for the XDR integer types.

    The :mod:`xdrlib2` module contains the preconstructed concrete subclasses
    that are defined in the XDR standard :rfc:`4506`.
    All concrete subclasses have the following read-only attributes:

    .. attribute:: min

       The minimum value (inclusive) accepted for the subclass

    .. attribute:: max

       The maximum value (exclusive) accepted for the subclass

    .. attribute:: signed

       Boolean value that indicates if the values
       for the subclass are signed or not.

    .. attribute:: packed_size

       Size (in bytes) for the encoding of values of the subclass.

    :class:`XdrInteger` subclasses the standard Python :class:`int` class.
    XdrInteger objects can therefore be used everywhere
    where a regular Python :class:`int` object is expected.
    A consequence of this is that when an :class:`XdrInteger` object
    is used in an expression, it is treated as a
    regular Pyhton :class:`int` object,
    and the resulting value is no longer an XDR type.
    """
    _mode = xdr_mode.ABSTRACT
    _parameters = ('min', 'max')
    _xdr_parameters = {'min': None,
                       'max': None,
                       'signed': None,
                       'packed_size': None}

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if parameters:
            if cls._mode is xdr_mode.FINAL:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
            xdr_parameters = cls._xdr_parameters.copy()
            extra_names = parameters.keys() - cls._parameters
            if extra_names:
                raise TypeError(f"unexpected class parameter(s) {extra_names!s} "
                                f"for class '{cls.__name__:s}'")
            missing_parameters = cls._parameters - xdr_parameters.keys()
            if missing_parameters:
                raise TypeError(f"missing class parameters {missing_parameters!s} "
                                f"for class '{cls.__name__:s}'")
            cls._xdr_parameters = xdr_parameters
            cls._xdr_parameters.update(parameters)

            if cls.max <= cls.min:
                raise ValueError(f"{cls.__name__:s}: minimum value ({cls.min:d}) "
                                 f"must be less than maximum value ({cls.max:d})")
            cls.signed = cls.min < 0
            size = (cls.max - cls.min).bit_length() - 1
            cls.packed_size = size // 8 + (1 if size % 8 else 0)
            cls._mode = xdr_mode.FINAL

    def __new__(cls, *args, **kwargs):
        if cls._mode is xdr_mode.ABSTRACT:
            raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")

        instance = super().__new__(cls, *args, **kwargs)
        if cls.min <= instance < cls.max:
            return instance
        else:
            raise OverflowError(f"Value {instance!r} is out of range for class {cls.__name__}.\n"
                                f"\tAllowed range is {cls.min:d} <= value < {cls.max:d}.")

    def __init__(self, *args, **kwargs):
        super().__init__()

    def _encode_(self):
        bstr = self.to_bytes(self.packed_size, XDR_BYTE_ORDER, signed=self.signed)
        return xdr_padded(bstr)

    @classmethod
    def _decode_(cls, bstr):
        size = cls.packed_size
        v_str, bstr = xdr_split_and_remove_padding(bstr, size)
        v = int.from_bytes(v_str, XDR_BYTE_ORDER, signed=cls.signed)
        return cls(v), bstr

    def __repr__(self):
        return f'{self.__class__.__name__:s}({super().__repr__():s})'


Int32 = XdrInteger.typedef('Int32', min=-1<<31, max=1<<31)
Integer = Int32.typedef('Integer')


Int32u = XdrInteger.typedef('Int32u', min=0, max=1<<32)
UnsignedInteger = Int32u.typedef('UnsignedInteger')


Int64 = XdrInteger.typedef('Int64', min=-1<<63, max=1<<63)
Hyper = Int64.typedef('Hyper')


Int64u = XdrInteger.typedef('Int64u', min=0, max=1<<64)
UnsignedHyper = Int64u.typedef('UnsignedHyper')
