# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.


from .xdr_integer import Integer, UnsignedInteger, Hyper, UnsignedHyper
from .xdr_enumeration import Enumeration
from .xdr_float import Float, Double, Quadruple


class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1


FALSE = Boolean.FALSE
TRUE = Boolean.TRUE


__all__ = [
    'Integer',
    'UnsignedInteger',
    'Hyper',
    'UnsignedHyper',
    'Enumeration',
    'Float',
    'Double',
    'Quadruple',
    'Boolean',
    'FALSE',
    'TRUE',
]
