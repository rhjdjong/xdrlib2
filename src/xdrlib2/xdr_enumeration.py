# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import xdr_mode, xdr_is_valid_name
from .xdr_integer import Integer


class Enumeration(Integer):
    _mode = xdr_mode.ABSTRACT
    _parameters = ()
    _enum_default_value = 0

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if parameters:
            if cls._mode is xdr_mode.FINAL:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
            cls._mode = xdr_mode.CONCRETE
            cls._enum_value_by_name = {}
            cls._enum_name_by_value = {}
            for name, value in parameters.items():
                if not xdr_is_valid_name(name):
                    raise ValueError(f"invalid enumeration identifier name '{name:s}' "
                                     f"for class '{cls.__name__:s}'")
                if name in cls._enum_value_by_name:
                    raise ValueError(f"Duplicate enumeration name '{name:s}' in class '{cls.__name__:s}'")
                if not cls._enum_value_by_name:
                    cls._enum_default_value = value
                cls._enum_value_by_name[name] = value
                if value not in cls._enum_name_by_value:
                    cls._enum_name_by_value[value] = name
            cls._mode = xdr_mode.FINAL

    def __new__(cls, value=None):
        if cls._mode is xdr_mode.ABSTRACT:
            raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")

        if value is None:
            value = cls._enum_default_value

        try:
            if isinstance(value, int):
                enum_name = cls._enum_name_by_value[value]
            else:
                enum_name = value
                value = cls._enum_value_by_name[enum_name]
        except KeyError:
            raise ValueError(f"invalid enumeration value '{value}' "
                             f"for enumeration '{cls.__name__:s}'") from None
        instance = super().__new__(cls, value)
        instance.name = enum_name
        return instance

    def __init__(self, value=None):
        super().__init__()

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls(cls._enum_value_by_name[name])
        except KeyError:
            return super()._getattr_(name)

    @classmethod
    def _getitem_(cls, index):
        if isinstance(index, str):
            return getattr(cls, index)
        return cls(list(cls._enum_value_by_name.values())[index])

    def __iter__(self):
        return self._enum_value_by_name.values()

    def __repr__(self):
        return f"{self.__class__.__name__:s}.{self.name:s}({super().__str__():s})"

    def __str__(self):
        return f"{self.name:s}({super().__str__():s})"


Boolean = Enumeration.typedef('Boolean', FALSE=0, TRUE=1)

# XDR semantics requiers that Enumeration names live in the same namespace
# as their Enumeration definition.
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE
