# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_integer import Integer
import re
import inspect
import itertools


class Enumeration(Integer):
    _final = False
    _abstract = True

    def __init_subclass__(cls, **kwargs):
        enum_list = []
        for n, v in cls._get_names_from_class_body().items():
            enum_list.append((n, v))
        for n, v in kwargs.items():
            enum_list.append((n, v))
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

        cls._enum_parameters = enum_map

        cls._abstract = False

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
            if name in vars(cls):
                raise ValueError(f"invalid (duplicate) enum identifier name '{name:s}' in class '{cls.__name__:s}'")
            enum_value = cls._make_enum_value(name, value)
            cls._enum_parameters[name] = enum_value
            setattr(cls, name, enum_value)
            if module_ns:
                if name in module_ns:
                    raise ValueError(f"duplicate enum identifier name '{name:s}' "
                                     f"in module '{module_ns['__name__']:s}'")
                module_ns[name] = enum_value
        cls._final = True

    @classmethod
    def _make_enum_value(cls, name, value):
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name):
            raise TypeError(f"invalid enumeration identifier name '{name:s}' for class '{cls.__name__:s}'")
        try:
            return cls(value)
        except ValueError:
            raise TypeError(f"invalid enumeration value {value!s} for '{cls.__name__:s}.{n:s}'")

    def __new__(cls, value=None):
        if cls._abstract:
            raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")
        if value is None:
            raise ValueError(f"enumeration type '{cls.__name__:s}' does not allow default instantiation.")

        if isinstance(value, str):
            try:
                return super().__new__(cls, cls._enum_parameters[value])
            except KeyError:
                raise ValueError(f"Invalid enumeration identifier name '{value:s}' "
                                 f"for enumeration '{cls.__name__:s}'") from None
        if isinstance(value, int):
            for enum_value in cls._enum_parameters.values():
                if enum_value == value:
                    return super().__new__(cls, enum_value)
        raise ValueError(f"Invalid value {value!r} for enumeration '{cls.__name__:s}'")


    @classmethod
    def _getattr(cls, name):
        try:
            return cls._enum_parameters[name]
        except KeyError:
            raise AttributeError(f"{cls.__class__.__name__:s} object '{cls.__name__:s}' "
                                 f"has no attribute '{name:s}'")

    def __repr__(self):
        return f"{self.__class__.__name__:s}({super().__str__():s})"

    def __str__(self):
        return super().__str__()

class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1

# Not strictly necessary, because the above Boolean class definition
# will have added FALSE and TRUE to this module's global namespace.
# Explicitly setting them here allows static analyzers, such as typically
# used by an IDE for code completion, to recognize these values as part of the module.
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE
