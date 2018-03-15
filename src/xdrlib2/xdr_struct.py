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
        if name in self._values:
            return self._values[name]
        raise AttributeError(f"{self.__class__.__name__:s} object "
                             f"has no attribute '{name:s}'")

    def __setattr__(self, name, value):
        if name == '_values':
            raise AttributeError(f"attribute '{name:s}' of '{self.__class__.__name__:s}' "
                                 f"object cannot be overwritten.")
        if self._values and name in self._values:
            self._values[name] = self._fields[name](value)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if name in self._values:
            raise AttributeError(f"attribute '{name:s}' of '{self.__class__.__name__:s}' object cannot be deleted.")
        super().__delattr__(name)

    def __init__(self, *args, **kwargs):
        super().__setattr__('_values', {})

        for (name, xdrtype), value in zip(self._fields.items(), args):
            self._values[name] = xdrtype(value)
        args = args[len(self._values):]

        for (name, xdrtype) in self._fields.items():
            if name not in self._values:
                if name in kwargs:
                    self._values[name] = xdrtype(kwargs[name])
                    del kwargs[name]
                else:
                    self._values[name] = xdrtype()
        if args:
            raise ValueError(f"too many initialization values for struct '{self.__class__.__name__:s}'. "
                             f"Expected {len(self._fields):d}, got {len(args) + len(kwargs):d}")
        if kwargs:
            raise ValueError(f"duplicate or invalid field name(s) "
                             f"for struct '{self.__class__.__name__:s}'")

    def encode(self):
        return b''.join(x.encode() for x in self._values.values())

    @classmethod
    def parse(cls, bstr):
        items = []
        for xdrtype in cls._fields.values():
            item, bstr = xdrtype.parse(bstr)
            items.append(item)
        return cls(*items), bstr

    def __eq__(self, other):
        if not type(self) == type(other):
            return False
        return all(getattr(self, n) == getattr(other, n) for n in self._names)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return f"{self.__class__.__name__:s}({', '.join(str(v) for v in self._values.values()):s})"

    def __str__(self):
        return ', '.join(str(v) for v in self._values.values())
