# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_integer import Integer
import re
import inspect
import itertools


class Enumeration(Integer):
    _final = False

    def __init_subclass__(cls, **kwargs):
        enum_list = []
        for n, v in cls._get_names_from_class_body().items():
            enum_list.append((n, cls._make_enum_value(n, v)))
        for n, v in kwargs.items():
            enum_list.append((n, cls._make_enum_value(n, v)))
        enum_map = {}
        for name, value in enum_list:
            if name in enum_map:
                raise TypeError(f"duplicate enum identifier name '{name:s}' "
                                 f"in class '{cls.__name__:s}'")
            else:
                enum_map[name] = value

        if cls._final:
            if enum_map:
                # This is subclassing a concrete enum type with additional items
                raise TypeError(f"cannot subclass '{cls.__name__:s}' enumeration type with modifications")
            return

        if not enum_map:
            raise TypeError(f"Enumeration subclass '{cls.__name__:s}' requires definition of enumeration values")

        cls._names = enum_map
        module_ns = None
        framelist = inspect.stack()
        # framelist[0] is current frame
        # framelist[1] is the calling frame for this subclass definition,
        # unless it is the 'typedef' classmethod. In that case
        # the module must be derived from the next calling frame
        if framelist[1].function == 'typedef':
            frame_info = framelist[2]
        else:
            frame_info = framelist[1]
        module_ns = frame_info.frame.f_globals

        for name, value in enum_map.items():
            # setattr(cls, name, value)
            if module_ns:
                if name in module_ns:
                    raise ValueError(f"duplicate enum identifier name '{name:s}' "
                                     f"in module '{module_ns['__name__']:s}'")
                module_ns[name] = value

        cls._final = True

    @classmethod
    def _make_enum_value(cls, name, value):
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name):
            raise TypeError(f"invalid enumeration identifier name '{name:s}' for class '{cls.__name__:s}'")
        try:
            return super().__new__(cls, value)
        except ValueError:
            raise TypeError(f"invalid enumeration value {value!s} for '{cls.__name__:s}.{n:s}'")

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
