# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_integer import Integer
import numbers


class Enumeration(Integer):
    _final = False
    _abstract = True
    _parameters = ()

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_creation_information(**kwargs)
        if cls._final:
            if parameters:
                raise TypeError(f"Cannot extend enumeration class '{cls.__name__:s}' "
                                f"with additional enumeration values {parameters!s}")
        else:
            if cls._abstract:
                if not parameters:
                    raise TypeError(f"Enumeration subclass '{cls.__name__:s}' "
                                    f"requires definition of enumeration values.")
                if '_enumeration_value' in vars(cls):
                    if parameters:
                        raise TypeError(f"{cls.__name:s}: redefinition of enumeration types not allowed.")
                else:
                    cls._abstract = False
                    cls._enumeration_value = {}
                    cls._enumeration_name = {}
                    for name, value in parameters.items():
                        if not cls._is_valid_xdr_name(name):
                            raise ValueError(f"invalid enumeration identifier name '{name:s}' "
                                             f"for class '{cls.__name__:s}'")
                        cls._enumeration_value[name] = value
                        cls._enumeration_name[value] = name
            cls._final = True

    def __new__(cls, value=None, **kwargs):
        if cls._abstract:
            if not kwargs:
                raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")
            return cls.typedef(**kwargs)

        arg = min(cls._enumeration_value.values()) if value is None else value

        if isinstance(arg, str):
            try:
                arg = getattr(cls, arg)
            except AttributeError:
                raise ValueError("invalid enumeration name '{value:s}' "
                                 "for enumeration '{cls.__name__:s}'") from None
        if isinstance(arg, numbers.Integral):
            if arg in cls._enumeration_name:
                return super().__new__(cls, arg)
        raise ValueError(f"invalid value {value!r} for enumeration '{cls.__name__:s}'") from None

    @classmethod
    def _getattr(cls, name):
        try:
            return cls(cls._enumeration_value[name])
        except KeyError:
            raise AttributeError(f"{cls.__class__.__name__:s} object '{cls.__name__:s}' "
                                 f"has no attribute '{name:s}'") from None

    def __repr__(self):
        return f"{self.__class__.__name__:s}({super().__str__():s})"

    def __str__(self):
        return super().__str__()


Boolean = Enumeration.typedef('Boolean', FALSE=0, TRUE=1)

# Not strictly necessary, because the above Boolean class definition
# will have added FALSE and TRUE to this module's global namespace.
# Explicitly setting them here allows static analyzers, such as typically
# used by an IDE for code completion, to recognize these values as part of the module.
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE
