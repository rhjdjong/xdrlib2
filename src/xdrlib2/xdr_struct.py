# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType

class Struct(XdrType):

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._final:
            if parameters:
                raise TypeError(f"cannot extend struct class '{cls.__name__:s}' "
                                f"with additional fields {parameters!s}")
        else:
            if cls._abstract:
                if not parameters:
                    raise TypeError(f"struct subclass '{cls.__name__:s}' "
                                    f"requires definition of fields.")
                if '_struct_field_type' in vars(cls):
                    if parameters:
                        raise TypeError(f"{cls.__name:s}: redefinition of struct types not allowed.")
                else:
                    cls._abstract = False
                    cls._struct_field_type = {}
                    for name, value in parameters.items():
                        if not cls._is_valid_xdr_name(name):
                            raise ValueError(f"invalid struct field name '{name:s}' "
                                             f"for class '{cls.__name__:s}'")
                        cls._struct_field_type[name] = value
            cls._final = True

    @classmethod
    def _getattr(cls, name):
        try:
            return cls(cls._struct_field_type[name])
        except KeyError:
            raise AttributeError(f"{cls.__class__.__name__:s} object '{cls.__name__:s}' "
                                 f"has no attribute '{name:s}'") from None

    def __getattr__(self, name):
        try:
            return self._struct_field[name]
        except KeyError:
            raise AttributeError(f"{self.__class__.__name__:s} object "
                             f"has no attribute '{name:s}'") from None

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            try:
                self._struct_field[name] = self._struct_field_type[name](value)
            except KeyError:
                raise AttributeError(f"attribute '{name:s}' of '{self.__class__.__name__:s}' "
                                     f"object cannot be written.") from None

    def __delattr__(self, name):
        if name.startswith('_'):
            super().__delattr__(name)
        else:
            if name in self._struct_field:
                self._struct_field[name] = None
            else:
                raise AttributeError(f"attribute '{name:s}' of '{self.__class__.__name__:s}' "
                                     f"object cannot be deleted.")

    def __new__(cls, *args, **kwargs):
        if cls._abstract:
            if not kwargs:
                raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")
            return cls.typedef(**kwargs)

        instance = super().__new__(cls)
        instance._struct_field = dict.fromkeys(cls._struct_field_type)
        return instance

    def __init__(self, *args, **kwargs):
        if len(args) > len(self._struct_field):
            raise ValueError(f"too many arguments for class '{self.__class__.__name__:s}'. "
                             f"Expected {len(self._struct_field):d}, got {len(args):d}")
        arguments = list(args[:len(self._struct_field_type)])
        for name in list(self._struct_field_type.keys())[len(args):]:
            arguments.append(kwargs.pop(name, None))
        if kwargs:
            raise ValueError(f"invalid keywords {kwargs.keys()!s} for class '{self.__class__.__name__:s}'")
        if len(arguments) != len(self._struct_field_type):
            raise ValueError(f"expected {len(self._struct_field_type):d} field values, "
                             f"got {len(arguments) + len(kwargs):d}.")

        for (name, typ), value in zip(self._struct_field_type.items(), arguments):
            self._struct_field[name] = typ(value)

    def encode(self):
        return b''.join(x.encode() for x in self._struct_field.values())

    @classmethod
    def parse(cls, bstr):
        items = []
        for xdrtype in cls._struct_field_type.values():
            item, bstr = xdrtype.parse(bstr)
            items.append(item)
        return cls(*items), bstr

    def __eq__(self, other):
        if not type(self) == type(other):
            return False
        return all(getattr(self, n) == getattr(other, n) for n in self._struct_field)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return f"{self.__class__.__name__:s}({', '.join(str(v) for v in self._struct_field.values()):s})"

    def __str__(self):
        return '{' + ', '.join(str(v) for v in self._struct_field.values()) + '}'
