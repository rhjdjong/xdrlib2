# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_integer import Integer
import re
import inspect
import itertools


class Enumeration(Integer):
    _final = False

    @classmethod
    def _init_concrete_subclass(cls, **kwargs):
        enum_list = []
        for key, value in list(vars(cls).items()):
            enum_value = cls._make_enum_value(key, value)
            if enum_value is not None:
                delattr(cls, key)
                enum_list.append((key, enum_value))
        for key, value in list(kwargs.items()):
            enum_value = cls._make_enum_value(key, value)
            if enum_value is not None:
                del kwargs[key]
                enum_list.append((key, enum_value))

        enum_map = {}
        for name, value in enum_list:
            if name in enum_map:
                raise ValueError(f"duplicate enum identifier name '{name:s}' "
                                 f"in class '{cls.__name__:s}'")
            else:
                enum_map[name] = value

        if cls._final and enum_map:
            # This is subclassing a concrete enum type with additional items
            raise TypeError(f"cannot subclass '{cls.__name__:s}' enumeration type with modifications")

        if not enum_map:
            return False, kwargs

        cls._names = enum_map
        module_ns = None
        framelist = inspect.stack()
        # framelist[0] is current frame
        # framelist[1] is the calling frame, i.e. the __init_subclass__ method called
        # for this subclass definition,
        # framelist[2] is the subclass definition itself
        # unless it is the 'typedef' classmethod. In that case
        # the module must be derived from the next calling frame
        if framelist[1].function == '__init_subclass__':
            if framelist[2].function == 'typedef':
                frame_info = framelist[3]
            else:
                frame_info = framelist[2]
        module_ns = frame_info.frame.f_globals

        for name, value in enum_map.items():
            # setattr(cls, name, value)
            if module_ns:
                if name in module_ns:
                    raise ValueError(f"duplicate enum identifier name '{name:s}' "
                                     f"in module '{module_ns['__name__']:s}'")
                module_ns[name] = value
        return True, kwargs

    @classmethod
    def _make_enum_value(cls, name, value):
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name):
            return None
        return super().__new__(cls, value)

    def __new__(cls, value=None):
        if value is None:
            # Use the first defined enumeration value
            for v in cls._names.values():
                value = v
                break

        if not cls._names:
            raise NotImplementedError(f"cannot instantiate values of abstract base class")
        if isinstance(value, str):
            try:
                return cls._names[value]
            except KeyError:
                raise ValueError(f"Invalid enumeration identifier name '{value:s}' "
                                 f"for enumeration '{cls.__name__:s}'") from None
        if isinstance(value, int):
            for enum_value in cls._names.values():
                if enum_value == value:
                    return enum_value
        raise ValueError(f"Invalid value {value!r} for enumeration '{cls.__name__:s}'")
