# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import inspect

class _MetaXdrType(type):
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
        if name in cls._names:
            return cls._names[name]
        raise AttributeError(f"{cls.__class__.__name__:s} object '{cls.__name__:s}' "
                             f"has no attribute '{name:s}'")


class XdrType(metaclass=_MetaXdrType):
    _final = False
    _parameters = {}
    _names = {}

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


    def __init_subclass__(cls, **kwargs):
        if cls._parameters or kwargs:
            modified = None

            parameters = cls._parameters.copy()
            # Check for parameters defined in the body of this class
            for param in list(parameters.keys()):
                if param in vars(cls):
                    if not inspect.ismethod(getattr(cls, param)):
                        parameters[param] = vars(cls)[param]
                        delattr(cls, param)
                    modified = True

            # Parameters in kwargs override parameters in the (super)class body
            for param in list(parameters.keys()):
                try:
                    kw_value = kwargs.pop(param)
                except KeyError:
                    pass
                else:
                    parameters[param] = kw_value
                    modified = True

            if modified:
                if cls._final:
                    raise TypeError(f"final class '{cls.__name__:s}' "
                                f"cannot be subclassed with modifications")
                else:
                    cls._parameters = parameters

            if not cls._final and all(v is not None for v in parameters.values()):
                cls._final, kwargs = cls._init_concrete_subclass(**kwargs)

        super().__init_subclass__(**kwargs)

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
    def typedef(cls, name=None, *bases, **kwargs):
        type_name = name if name else '_'
        new_type = cls.__class__(type_name, (cls,) + bases, kwargs)
        return new_type


class XdrAtomic(XdrType):
    _packed_size = None

    @classmethod
    def packed_size(cls):
        return cls._packed_size


class Void(XdrType):
    def __new__(cls, _=None):
        return super().__new__(cls)

    def encode(self):
        return b''

    @classmethod
    def parse(cls, bstr):
        return cls(), bstr

    def __eq__(self, other):
        return other is None or isinstance(other, Void)

    def __ne__(self, other):
        return not self == other

