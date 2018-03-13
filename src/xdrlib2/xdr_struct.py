# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType

class Struct(XdrType):

    def __init_subclass__(cls, **kwargs):
        names = cls._get_names_from_class_body()
        fields = {}
        for name, value in names.items():
            if not name.startswith('_'):
                fields[name] = value
        for name, value in kwargs.items():
            if name in fields:
                raise ValueError(f"duplicate field name '{name:s}' in '{cls.__name__:s}' struct")
            fields[name] = value

        if cls._final:
            if fields:
                # This is subclassing a concrete enum type with additional items
                raise TypeError(f"cannot subclass '{cls.__name__:s}' with modifications")

        if fields:
            if not all(v is not None for v in fields.values()):
                raise TypeError(f"incomplete instantiation of XdrInteger subclass '{cls.__name__:s}'")
            cls._fields = fields
            cls._final = True

    def __getattr__(self, name):
        if name in self._names:
            return self._names[name]
        raise AttributeError(f"{self.__class__.__name__:s} object "
                             f"has no attribute '{name:s}'")

    def __init__(self, *args, **kwargs):
        self._names = {}

        name_type = self._fields.items()
        for (name, xdrtype), value in zip(name_type, args):
            self._names[name] = xdrtype(value)
        for (name, xdrtype) in name_type:
            if name in kwargs:
                self._names[name] = xdrtype(kwargs[name])
                del kwargs[name]
            else:
                self._names[name] = xdrtype()
        if kwargs:
            raise ValueError(f"duplicate or invalid field name(s) for struct '{self.__class__.__name__:s}'")



