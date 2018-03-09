# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.


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


class XdrType(metaclass=_MetaXdrType):
    _final = False

    def __init_subclass__(cls, **kwargs):
        if hasattr(cls, '_parameter_names'):
            parameters = {}
            var_map = vars(cls)
            for name in cls._parameter_names:
                if name in var_map:
                    parameters[name] = var_map[name]
                    delattr(cls, name)
                if '_' + name in var_map:
                    parameters[name] = var_map['_' + name]
            for name in cls._parameter_names:
                kw_value = kwargs.get(name)
                if parameters.get(name) is None:
                    if kw_value is not None:
                        parameters[name] = kw_value
                else:
                    if kw_value is not None:
                        raise TypeError(f"'{cls.__name__:s}' subclass has multiple '{name:s}' parameters")
            if cls._final and parameters:
                raise TypeError(f"'{cls.__name__:s}' class cannot be subclassed with modifications")
            for name, value in parameters.items():
                setattr(cls, '_' + name, value)
        super().__init_subclass__()

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
        return size + ((size % 4) % 4)

    @staticmethod
    def remove_padding(bstr, size):
        if any(b for b in bstr[size:]):
            raise ValueError("non-zero padding byte(s) encountered: '{bstr[size:].encode('utf8'):s}'")
        return bstr[:size]

    @classmethod
    def typedef(cls, name=None, **kwargs):
        type_name = name if name else '_'
        new_type = type(type_name, (cls,), kwargs)
        return new_type


class XdrAtomic(XdrType):
    _packed_size = None

    @classmethod
    def packed_size(cls):
        return cls._packed_size
