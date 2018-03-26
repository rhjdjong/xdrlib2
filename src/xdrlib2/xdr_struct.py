# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType, _xdr_mode
from .xdr_optional import Optional

class Struct(XdrType, dict):
    _mode = _xdr_mode.ABSTRACT

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
        cls._struct_field_type = {}
        if not kwargs:
            cls._mode = _xdr_mode.CONCRETE  # Allow for later additions
        else:
            for name, value in kwargs.items():
                cls._set_field_type(name, value)
            cls._mode = _xdr_mode.FINAL


    @classmethod
    def _set_field_type(cls, name, value):
        if not cls._is_valid_xdr_name(name):
            raise ValueError(f"invalid struct field name '{name:s}' "
                             f"for class '{cls.__name__:s}'")
        if not issubclass(value, XdrType):
            raise TypeError(f"invalid struct type {name:s}={value!s} "
                            f"for class '{cls.__name__:s}'")
        cls._struct_field_type[name] = value

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls._struct_field_type[name]
        except KeyError:
            return super()._getattr_(name)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"{self.__class__.__name__:s} object "
                                 f"has no attribute '{name:s}'") from None

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif self.__class__._mode is _xdr_mode.CONCRETE:
            self._set_field_type(name, value)
        else:
            try:
                item_type = self._struct_field_type[name]
            except KeyError:
                raise AttributeError(f"attribute '{name:s}' of '{self.__class__.__name__:s}' "
                                     f"object cannot be written.") from None
            self[name] = item_type(value)

    def __delattr__(self, name):
        if name.startswith('_'):
            super().__delattr__(name)
        else:
            try:
                item_type = self._struct_field_type[name]
            except KeyError:
                raise AttributeError(name) from None
            if issubclass(item_type, Optional):
                self._struct_field[name] = None
            else:
                raise AttributeError(f"attribute '{name:s}' of '{self.__class__.__name__:s}' "
                                     f"object cannot be deleted.")

    def __new__(cls, *args, **kwargs):
        if cls._mode is _xdr_mode.ABSTRACT:
            if args:
                raise TypeError(f"cannot subclass '{cls.__name__:s}' class with positional arguments")
            return cls.typedef(**kwargs)
        if not kwargs and len(args) == 1 and isinstance(args[0], cls):
            return super().__new__(cls, **args[0])
        else:
            return super().__new__(cls, *args, **kwargs)


    def __init__(self, *args, **kwargs):
        if len(args) > len(self._struct_field_type):
            raise ValueError(f"too many arguments for class '{self.__class__.__name__:s}'. "
                             f"Expected {len(self._struct_field_type):d}, got {len(args):d}")
        for (name, typ), value in zip(self._struct_field_type.items(), args):
            self[name] = typ(value)
        for name, value in kwargs.items():
            if name in self:
                raise ValueError(f"duplicate assignment for field '{name:s}' "
                                 f"for '{self.__class__.__name__:s}' object'")
            try:
                typ = self._struct_field_type[name]
            except KeyError:
                raise ValueError(f"invalid element '{name:s}' "
                                 f"for class '{self.__class__.__name__:s}' object") from None
            self[name] = typ(value)
        for name, typ in self._struct_field_type.items():
            if name not in self:
                self[name] = typ()

    def encode(self):
        return b''.join(self[name].encode() for name in self._struct_field_type.keys())

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
        return all(self[n] == other[n] for n in self._struct_field_type.keys())

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return f"{self.__class__.__name__:s}({', '.join(str(v) for v in self.values()):s})"

    # def __str__(self):
    #     return '{' + ', '.join(str(v) for v in self._struct_field.values()) + '}'
