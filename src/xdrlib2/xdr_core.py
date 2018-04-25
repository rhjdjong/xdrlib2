# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import numbers
import abc
import re
import enum


XDR_UNIT_SIZE = 4
XDR_BYTE_ORDER = 'big'


reserved_names = (
    'bool',
    'case',
    'const',
    'default',
    'double',
    'quadruple',
    'enum',
    'float',
    'hyper',
    'int',
    'opaque',
    'string',
    'struct',
    'switch',
    'typedef',
    'union',
    'unsigned',
    'void',
)


def xdr_padded(bstr):
    return bstr + xdr_padding(len(bstr))


def xdr_padded_size(size):
    return size + xdr_padding_size(size)


def xdr_padding(size):
    return b'\0' * xdr_padding_size(size)


def xdr_padding_size(size):
    return ((XDR_UNIT_SIZE - size % XDR_UNIT_SIZE) % XDR_UNIT_SIZE)


def xdr_split_and_remove_padding(bstr, size):
    padded_size = xdr_padded_size(size)
    if len(bstr) < padded_size:
        raise ValueError(f"byte sequence too short. "
                         f"Expected {padded_size:d} bytes, "
                         f"got {len(bstr):d} bytes.")
    if any(b for b in bstr[size:padded_size]):
        raise ValueError(f"non-zero padding byte(s) encountered: {bstr[size:padded_size]!s}'")
    return bstr[:size], bstr[padded_size:]


def xdr_is_valid_name(name):
    if name in reserved_names:
        return False
    return re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name)


xdr_mode = enum.Enum('xdr_mode', 'ABSTRACT CONCRETE FINAL')


def encode(x):
    return x._encode_()


def decode(cls, bstr):
    obj, rest = cls._decode_(bstr)
    if rest != b'':
        raise ValueError(f"input contains additional data '{rest}'")
    return obj


def _is_valid_xdr_name(name):
    if name in reserved_names:
        return False
    return re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name)


class _MetaXdrType(abc.ABCMeta):
    # Concrete XDR types contain parameters that determine the
    # allowed values and operations.
    # To prevent inadvertent modifications of these parameters,
    # creating, modifying, or deleting these parameters is not allowed.
    # def __setattr__(cls, name, value):
    #     if cls._mode is xdr_mode.FINAL:
    #         raise AttributeError(f"cannot set attribute '{name:s}' to '{value}' for class '{cls.__name__:s}'")
    #     if name.startswith('_'):
    #         super().__setattr__(name, value)
    #     else:
    #         cls._setattr_(name, value)
    #
    # def __delattr__(cls, name):
    #     if cls._mode is xdr_mode.FINAL:
    #         raise AttributeError(f"cannot delete attribute '{name:s}' from class '{cls.__name__:s}'")
    #     super().__delattr__(name)

    # Concrete classes expose their parameters as class attributes.
    # Some classes, e.g. structs and unions, also expose their members as class attributes.
    # Name resolution is delegated to the class method '_getattr_' (single underscores).
    def __getattr__(cls, name):
        return cls._getattr_(name)

    def __setattr__(cls, name, value):
        if name in cls._xdr_parameters:
            if cls._mode is xdr_mode.FINAL:
                raise AttributeError(f"cannot set xdr parameter '{name:s}' to {value!r} "
                                     f"for class '{cls.__name__:s}'")
            cls._xdr_parameters[name] = value
        elif xdr_is_valid_name(name):
            cls._setattr_(name, value)
        else:
            super().__setattr__(name, value)

    def __delattr__(cls, name):
        if name in cls._xdr_parameters:
            if cls._mode is xdr_mode.FINAL:
                raise AttributeError(f"Cannot delete xdr parameter '{name:s}' "
                                     f"for class '{cls.__name__:s}'")
            cls._xdr_parameters[name] = None
        else:
            super().__delattr__(name)

    def __getitem__(cls, index):
        return cls._getitem_(index)

    def __enter__(cls):
        if cls._mode is not xdr_mode.CONCRETE:
            raise TypeError(f"context expression '{cls.__name__:s}' "
                            f"must be an XDR class being constructed")
        return cls

    def __exit__(cls, exc_type, exc_value, exc_traceback):
        if cls._mode is not xdr_mode.FINAL:
            cls._mode = xdr_mode.FINAL


class XdrType(metaclass=_MetaXdrType):
    _mode = xdr_mode.ABSTRACT
    _parameters = ()    # Parameters used by an XDR factory class
    _xdr_parameters = {}
    _optional_level = 0
    _optional = False

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls._xdr_parameters[name]
        except KeyError:
            raise AttributeError(f"'{cls.__class__.__name__:s}' object '{cls.__name__:s}' "
                                 f"has no attribute '{name:s}'") from None

    @classmethod
    def _setattr_(cls, name, value):
        if cls._mode is xdr_mode.FINAL:
            raise AttributeError(f"cannot set attribute '{name:s}' in final class '{cls.__name__:s}'")
        cls._xdr_parameters[name] = value

    def __getattr__(self, name):
        return getattr(self.__class__, name)

    @classmethod
    def _getitem_(cls, index):
        raise TypeError(f"class '{cls.__name__:s}' is not subscriptable")

    @classmethod
    def _get_class_parameters(cls, **kwargs):
        """
        This method obtains the parameters from the class body
        (any attribute that does not start with an underscore)
        and the kwargs parameter in the argument.
        The parameters found in the class body are removed from the body,
        to avoid conflicts with e.g. class properties with the same name.
        """
        cls_vars = vars(cls).copy()
        parameters = {}
        for name, value in cls_vars.items():
            if cls._is_xdr_class_parameter(name, value):
                parameters[name] = value
                delattr(cls, name)
        duplicate_names = parameters.keys() & kwargs.keys()
        if duplicate_names:
            raise TypeError(f"class '{cls.__name__:s}' got duplicate class parameter(s) '{duplicate_names!s}")
        parameters.update(kwargs)
        return parameters

    @classmethod
    def _is_xdr_class_parameter(cls, name, value):
        if name.startswith('_'):
            return False
        if name in cls._parameters:
            return True
        if isinstance(value, (numbers.Number, str)):
            return True
        try:
            return issubclass(value, XdrType)
        except TypeError:
            return False

    def _encode_(self):
        raise NotImplementedError

    @classmethod
    def _decode_(cls, bstr):
        raise NotImplementedError

    @classmethod
    def typedef(cls, _xdr_type_name=None, *bases, **kwargs):
        type_name = _xdr_type_name if _xdr_type_name else cls.__name__
        new_type = cls.__class__(type_name, (cls,) + bases, {}, **kwargs)
        return new_type

    def _eq_class(self, other):
        return type(self) == type(other)
