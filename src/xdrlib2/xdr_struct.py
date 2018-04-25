# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType, xdr_mode, xdr_is_valid_name
from .xdr_union import Optional

class Struct(XdrType, dict):
    _mode = xdr_mode.ABSTRACT

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if parameters:
            if cls._mode is xdr_mode.FINAL:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
        cls._struct_field_type = {}
        if not parameters:
            if cls._mode is xdr_mode.ABSTRACT:
                cls._mode = xdr_mode.CONCRETE  # Allow for later additions
        else:
            for name, value in parameters.items():
                cls._set_field_type(name, value)
            cls._mode = xdr_mode.FINAL


    @classmethod
    def _set_field_type(cls, name, value):
        if not xdr_is_valid_name(name):
            raise ValueError(f"invalid field name '{name:s}' "
                             f"for struct '{cls.__name__:s}'")
        if name in cls._struct_field_type:
            raise TypeError(f"duplicate field name '{name:s}' for struct '{cls.__name__:s}'")
        if not issubclass(value, XdrType):
            raise TypeError(f"invalid field {name:s}={value!s} "
                            f"for struct '{cls.__name__:s}'")
        cls._struct_field_type[name] = value

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls._struct_field_type[name]
        except KeyError:
            return super()._getattr_(name)

    @classmethod
    def _getitem_(cls, index):
        try:
            return cls._struct_field_type[index]
        except KeyError:
            return super()._getitem_(index)

    @classmethod
    def _setattr_(cls, name, value):
        if cls._mode is xdr_mode.CONCRETE:
            cls._set_field_type(name, value)
        else:
            raise AttributeError(name)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"{self.__class__.__name__:s} object "
                                 f"has no attribute '{name:s}'") from None

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
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
                self._struct_field[name] = item_type(None)
            else:
                raise AttributeError(f"attribute '{name:s}' of '{self.__class__.__name__:s}' "
                                     f"object cannot be deleted.")

    def __init__(self, *args, **kwargs):
        if self.__class__._mode is xdr_mode.ABSTRACT:
            raise NotImplementedError(f"cannot instantiate abstract '{self.__class__.__name__:s}' class")

        if len(args) == 1 and not kwargs:
            if isinstance(args[0], self.__class__):
                self.update(args[0])
            return

        if len(args) > len(self._struct_field_type):
            raise ValueError(f"too many arguments for class '{self.__class__.__name__:s}'. "
                             f"Expected {len(self._struct_field_type):d}, got {len(args):d}")
        for (name, typ), value in zip(self._struct_field_type.items(), args):
            self[name] = value if isinstance(value, typ) else typ(value)

        for name, typ in list(self._struct_field_type.items())[len(self):]:
            v = kwargs.pop(name, None)
            if v is not None:
                self[name] = v if isinstance(v, typ) else typ(v)
            else:
                self[name] = typ()

    def _encode_(self):
        return b''.join(element._encode_() for element in self.values())

    @classmethod
    def _decode_(cls, bstr):
        items = []
        for xdrtype in cls._struct_field_type.values():
            item, bstr = xdrtype._decode_(bstr)
            items.append(item)
        return cls(*items), bstr

    def __eq__(self, other):
        if not self._eq_class(other):
        # if not type(self) == type(other):
            return False
        return all(self[n] == other[n] for n in self._struct_field_type.keys())

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return f"{self.__class__.__name__:s}({', '.join(str(v) for v in self.values()):s})"

    def __str__(self):
        return '{' + ', '.join(str(v) for v in self.values()) + '}'
