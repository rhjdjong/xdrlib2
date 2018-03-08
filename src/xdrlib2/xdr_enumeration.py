# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_integer import Integer
import re
import inspect
import itertools


class Enumeration(Integer):
    _final = False
    _parameter_names = ()
    _enum_map = None

    def __init_subclass__(cls, **name_value_map):
        super().__init_subclass__()
        enum_list = []
        for key, value in itertools.chain(vars(cls).items(), name_value_map.items()):
            enum_value = cls._make_enum_value(key, value)
            if enum_value is not None:
                enum_list.append((key, enum_value))
        enum_map = {}
        for name, value in enum_list:
            if name in enum_map:
                raise ValueError(f"duplicate enum identifier name '{name:s}' "
                                 f"in class '{cls.__name__:s}'")
            else:
                enum_map[name] = value

        if cls._enum_map and enum_map:
            # This is subclassing a concrete enum type with additional items
            raise TypeError(f"cannot subclass '{cls.__name__:s}' enumeration type with modifications")

        cls._enum_map = enum_map

        framelist = inspect.stack()
        # framelist[0] is current frame
        # framelist[1] is the calling frame, i.e. the subclass definition
        module_ns = framelist[1].frame.f_globals

        for name, value in cls._enum_map.items():
            setattr(cls, name, value)
            if name in module_ns:
                raise ValueError(f"duplicate enum identifier name '{name:s}' "
                                 f"in module '{module_ns['__name__']:s}'")
            module_ns[name] = value
        cls._final = True

    @classmethod
    def _make_enum_value(cls, name, value):
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name):
            return None
        return super().__new__(cls, value)

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
