# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_integer import Integer
import re
import inspect


class _XdrMetaEnumeration(type):
    def __init__(cls, name, bases, ns, **kwargs):
        cls._enum_map = {}
        for name, value in list(ns.items()):
            if not name.startswith('_'):
                cls._create_enum_item(name, value)
                del (ns[name])
        for name, value in kwargs.items():
            if not name.startswith('_'):
                cls._create_enum_item(name, value)
        super().__init__(name, bases, ns)
        if cls._enum_map:
            cls._frozen = True

    def __setattr__(cls, name, value):
        if cls._frozen:
            raise AttributeError(f"cannot set or modify attributes of '{cls.__name__:s}' enumeration class")
        super().__setattr__(name, value)


class Enumeration(Integer, metaclass=_XdrMetaEnumeration):
    _enum_map = None
    _frozen = None

    @classmethod
    def _create_enum_item(cls, name, value):
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name):
            raise ValueError(f"invalid enum identifier name '{name:s}' in class {cls.__name__:s}")
        if name in cls._enum_map:
            raise AttributeError(f"enum identifier name '{name:s}' "
                                 f"is already present in in class '{cls.__name__:s}'")
        if name in cls._module_ns:
            raise AttributeError(f"enum identifier name '{name:s}' "
                                 f"is already present in module '{__name__:s}'")
        enum_value = super().__new__(cls, value)
        cls._enum_map[name] = enum_value
        setattr(cls, name, enum_value)
        cls._module_ns[name] = enum_value

    def __init_subclass__(cls, **name_value_map):
        if cls._enum_map:
            raise TypeError(f"cannot subclass '{cls.__name__:s}' enumeration type")

        for attr in list(cls.__dict__):
            if not attr.startswith('_'):
                setattr(cls, '_' + attr, getattr(cls, attr))

        framelist = inspect.stack()
        # framelist[0] is current frame
        # framelist[1] is the calling frame, i.e. the subclass definition
        cls._module_ns = framelist[1].frame.f_globals

    def __new__(cls, value):
        if not cls._enum_map:
            raise NotImplementedError(f"cannot instantiate values of abstract base class")
        if isinstance(value, str):
            try:
                return cls._enum_map[value]
            except KeyError:
                raise ValueError(f"Invalid enumeration identifier name '{value:s}' "
                                 f"for enumeration '{cls.__name__:s}'") from None
        if isinstance(value, int):
            for enum_value in cls._enum_map.values():
                if enum_value == value:
                    return enum_value
        raise ValueError(f"Invalid value {value!r} for enumeration '{cls.__name__:s}'")
