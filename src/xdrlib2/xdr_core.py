# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import numbers
import abc
import re
import enum
import copy

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


def encode(xdr_object):
    """
    :param xdr_object: The XDR object to encode
    :return: bytes

    :func:`encode` encodes :obj:`xdr_object` according
    to the XDR standard, and returns a :class:`bytes` object
    that contains the result of the encoding.
    It does this by calling the :meth:`_encode_` method
    on :obj:`xdr_object`.
    """
    return xdr_object._encode_()


def decode(xdr_class, bytestr):
    """
    :param xdr_class: The XDR class for the resulting XDR object
    :param bytestr: A byte string with the XDR-encoded data for the XDR object
    :return: an :class:`xdr_class` instance.
    :raises TypeError: when bytestr does not contain a valid
                       encoded :class:`xdr_class` object.
    :raises ValueError: when bytestr contains more bytes than required for the
                        construction of an :class:`xdr_class` object.

    :func:`decode` constructs an instance of :class:`xdr_class`
    from the encoded data in :obj:`bytestr`.
    It does this by calling the :meth:`_decode_` method
    on :class:`xdr_class`.

    """
    obj, rest = xdr_class._decode_(bytestr)
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
    """
    :class:`XdrType` is the abstract base class for all other XDR types.

    It defines the following methods that are available in all XDR types:

    .. automethod:: xdrlib2.XdrType._encode_
    .. automethod:: xdrlib2.XdrType._decode_
    .. automethod:: xdrlib2.XdrType.typedef
    """
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
        """
        Produces a :class:`bytes` object with the XDR-encoded version of the current object.

        :return: :class:`bytes`
        """
        raise NotImplementedError

    @classmethod
    def _decode_(cls, bytestr):
        """
        Return a decoded XDR object and the remainder of :obj:`bytestr`.

        :param bytestr: A :class:`bytes`-like object containing an XDR-encoded object.
        :return: (xdr_object, bytestr)

            *  :obj:`xdr_object` is the XDR object decoded from the
               original :obj:`bytestr`.
            *  :obj:`bytestr` contains the unused trailing bytes from
               the original :obj:`bytestr`

        :raises TypeError: when the contents of :obj:`bytestr` do not correspond
                           to an XDR-encoded object of the current XDR class.
        """
        raise NotImplementedError

    @classmethod
    def typedef(cls, xdr_type_name=None, *bases, **parameters):
        """
        Create a derived XDR class.

        :param xdr_type_name: The name for the derived class.
                               If `None` or not specified, the derived class
                               will have the same name as the current class.
        :param bases: Any additional base classes
                      for the derived class.
        :param parameters: Any parameters relevant for the creation of the derived class.
                       Which parameters are valid depends on the current class.
                       This is documented with each (abstract) XDR subclass in this module.
        :return: An XDR class that is a subclass of the current class.
                 When no `bases` and no `parameters` are supplied,
                 the resulting XDR class is simply a copy of the current XDR class.
        :raises TypeError: when invalid parameters are supplied for
                           a subclass of the current class.
        """
        type_name = xdr_type_name if xdr_type_name else cls.__name__
        new_type = cls.__class__(type_name, (cls,) + bases, {}, **parameters)
        return new_type

    def _eq_class(self, other):
        return type(self) == type(other)
