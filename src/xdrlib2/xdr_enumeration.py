# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import _xdr_mode, xdr_is_valid_name
from .xdr_integer import Integer
import numbers


class Enumeration(Integer):
    _mode = _xdr_mode.ABSTRACT
    _parameters = ()

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._mode is _xdr_mode.FINAL:
            if parameters:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
        if cls._mode is _xdr_mode.ABSTRACT:
            cls._init_abstract_subclass_(**parameters)
        else:
            cls._init_concrete_subclass_(**parameters)

    @classmethod
    def _init_abstract_subclass_(cls, **kwargs):
        if kwargs:
            cls._mode = _xdr_mode.CONCRETE
            cls._enum_value_by_name = {}
            cls._enum_value_by_value = {}
            for name, value in kwargs.items():
                if not xdr_is_valid_name(name):
                    raise ValueError(f"invalid enumeration identifier name '{name:s}' "
                                     f"for class '{cls.__name__:s}'")
                enum_value = cls(value)
                enum_value.name = name
                cls._enum_value_by_name[name] = enum_value
                cls._enum_value_by_value[value] = enum_value
            cls._mode = _xdr_mode.FINAL

    def __new__(cls, value=None, **kwargs):
        if cls._mode is _xdr_mode.ABSTRACT:
            if not kwargs:
                raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")
            return cls.typedef(**kwargs)

        if cls._mode is _xdr_mode.CONCRETE:
            if value is None:
                raise ValueError(f"concrete enumeration member definition for "
                                 f"'{cls.__name__:s}' class requires value")
            return super().__new__(cls, value, **kwargs)
        else:
            arg = min(cls._enumeration_value.values()) if value is None else value

            if isinstance(arg, str):
                try:
                    instance = super().__new__(cls, cls._enum_value_by_name[arg])
                except KeyError:
                    raise ValueError("invalid enumeration name '{value:s}' "
                                     "for enumeration '{cls.__name__:s}'") from None
                instance.name = arg
                return instance

            if isinstance(arg, numbers.Integral):
                try:
                    instance = super().__new__(cls, cls._enum_value_by_value[arg])
                except KeyError:
                    raise ValueError("invalid enumeration name '{value:s}' "
                                     "for enumeration '{cls.__name__:s}'") from None
                instance.name = list(n for n, v in cls._enum_value_by_name.items() if v == arg)[0]
                return instance

            raise ValueError(f"invalid value {value!r} for enumeration '{cls.__name__:s}'") from None

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls._enum_value_by_name[name]
        except KeyError:
            return super()._getattr_(name)

    def __repr__(self):
        return f"{self.__class__.__name__:s}.{self.name:s}({super().__str__():s})"

    def __str__(self):
        return f"{self.name:s}({super().__str__():s})"


Boolean = Enumeration.typedef('Boolean', FALSE=0, TRUE=1)

# XDR semantics requiers that Enumeration names live in the same namespace
# as their Enumeration definition.
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE
