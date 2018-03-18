# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import inspect
import re

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

class _MetaXdrType(type):
    def __init__(cls, name, bases, dct, **kwargs):
        super().__init__(name, bases, dct, **kwargs)
        # Execute class-specific initialization
        cls._init_class(dct, **kwargs)

    # Concrete XDR types contain parameters that determine the
    # allowed values and operations.
    # To prevent inadvertent modifications of these parameters,
    # creating, modifying, or deleting these parameters is not allowed.
    def __setattr__(cls, name, value):
        if cls._final:
            raise AttributeError(f"cannot set attribute '{name:s}' to '{value}' for class '{cls.__name__:s}'")
        super().__setattr__(name, value)

    def __delattr__(cls, name):
        if cls._final:
            raise AttributeError(f"cannot delete attribute '{name:s}' from class '{cls.__name__:s}'")
        super().__delattr__(name)

    def __getattr__(cls, name):
        return cls._getattr(name)
        # if name in cls._names:
        #     return cls._names[name]
        # raise AttributeError(f"{cls.__class__.__name__:s} object '{cls.__name__:s}' "
        #                      f"has no attribute '{name:s}'")

    def __getitem__(cls, index):
        return cls._get_item(index)


class XdrType(metaclass=_MetaXdrType):
    _final = False
    _abstract = True
    _parameters = ()

    @classmethod
    def _init_class(cls, dct, **kwargs):
        pass

    @classmethod
    def _create_anonymous_subclass(cls, *args, **kwargs):
        if args:
            raise ValueError(f"Cannot instantiate abstract class {cls.__name__:s} for {args!s}")
        return cls.typedef(**kwargs)

    @classmethod
    def _validate_arguments(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def _get_item(cls, index):
        raise NotImplementedError(f"class '{cls.__name__:s}' does not support indexing.")

    @classmethod
    def _get_class_creation_information(cls, **kwargs):
        if cls._final:
            if kwargs:
                # This is subclassing a concrete type with additional or modified parameters
                raise TypeError(f"cannot subclass '{cls.__name__:s}' type with modifications")
            return {}  # Subclassing without modifications is OK

        parameters = {n: v for n, v in vars(cls).items() if not n.startswith('_')}
        for n in kwargs:
            if n in parameters:
                raise ValueError(f"class '{cls.__name__:s}' got duplicate class parameter '{n:s}'")
        parameters.update(kwargs)

        if cls._final and parameters:
            raise TypeError(f"cannot subclass '{cls.__name__:s}' type with modifications")

        for n in parameters:
            if n in vars(cls):
                delattr(cls, n)
        return parameters

    @classmethod
    def _get_names_from_class_body(cls, *args):
        parameters = {}
        class_body = vars(cls)
        for name, value in class_body.items():
            if not name.startswith('_'):
                if name in parameters:
                    raise ValueError(f"duplicate name '{name:s}' in class '{cls.__name__:s}'")
                parameters[name] = value

        if args:
            unexpected_parameters = set(parameters.keys()) - set(args)
            if unexpected_parameters:
                raise ValueError(f"unexpected parameter(s) for '{cls.__name__:s}': "
                                f"{tuple(unexpected_parameters)!s} ")
        for name in parameters:
            delattr(cls, name)
        return parameters



    @classmethod
    def _init_concrete_subclass(cls, **kwargs):
        raise NotImplementedError(f"concrete subclass '{cls.__name__:s}'"
                                  f"must override class method '_init_concrete_subclass'")

    @classmethod
    def decode(cls, bstr):
        obj, rest = cls.parse(bstr)
        if rest != b'':
            raise ValueError(f"input contains additional data '{rest}'")
        return obj

    @staticmethod
    def _is_valid_xdr_name(name):
        if name in reserved_names:
            return False
        return re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name)


    @staticmethod
    def padding(size):
        return b'\0' * ((4 - size % 4) % 4)

    @staticmethod
    def padded_size(size):
        return size + ((4 - size % 4) % 4)

    @staticmethod
    def remove_padding(bstr, size):
        if any(b for b in bstr[size:]):
            raise ValueError("non-zero padding byte(s) encountered: '{bstr[size:].encode('utf8'):s}'")
        return bstr[:size]

    @classmethod
    def typedef(cls, _xdr_type_name=None, *bases, **kwargs):
        type_name = _xdr_type_name if _xdr_type_name else cls.__name__
        new_type = cls.__class__(type_name, (cls,) + bases, {}, **kwargs)
        return new_type


class XdrAtomic(XdrType):
    _packed_size = None

    def __new__(cls, *args, **kwargs):
        if cls._abstract:
            raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")
        return super().__new__(cls, *args, **kwargs)

    @classmethod
    def _validate_arguments(cls, *args, **kwargs):
        pass  # Validation is best done during instance creation.

    @classmethod
    def packed_size(cls):
        return cls._packed_size


class Void(XdrType):
    _final = True
    _abstract = False

    def __new__(cls, _=None):
        return super().__new__(cls)

    @classmethod
    def _validate_arguments(cls):
        pass

    def encode(self):
        return b''

    @classmethod
    def parse(cls, bstr):
        return cls(), bstr

    def __eq__(self, other):
        return other is None or isinstance(other, Void)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return f"{self.__class__.__name__:s}()"

    def __str__(self):
        return 'None'
