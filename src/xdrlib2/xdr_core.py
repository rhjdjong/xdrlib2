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

    def __getattr__(cls, name):
        if not name.startswith('_') and name in cls._name_map:
            return cls._name_map[name]
        return super().__getattr__(name)


class XdrType(metaclass=_MetaXdrType):
    _final = False
    _name_map = {}

    def __init_subclass__(cls, **kwargs):
        if hasattr(cls, '_parameter_names'):
            modified = False

            # Check for parameters defined in the body of this class
            for name in cls._parameter_names:
                if name in vars(cls) and not callable(getattr(cls, name)):
                    setattr(cls, '_' + name, vars(cls)[name])
                    delattr(cls, name)
                    modified = True

            # Parameters in kwargs override parameters in the (super)class body
            for name in cls._parameter_names:
                try:
                    kw_value = kwargs.pop(name)
                except KeyError:
                    pass
                else:
                    setattr(cls, '_' + name, kw_value)
                    modified = True

            if cls._final and modified:
                raise TypeError(f"final class '{cls.__name__:s}' "
                                f"cannot be subclassed with modifications")

            if not cls._final and all(vars(cls).get('_' + name) is not None for name in cls._parameter_names):
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
