# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.


class _MetaXdrType(type):
    def __setattr__(cls, name, value):
        if cls._frozen:
            raise AttributeError(f"cannot set attribute '{name:s}' to '{value}' for class '{cls.__name__:s}'")
        super().__setattr__(name, value)


class XdrType(metaclass=_MetaXdrType):
    _frozen = True


