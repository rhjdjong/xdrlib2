# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.


from .xdr_integer import Integer, UnsignedInteger, Hyper, UnsignedHyper
from .xdr_enumeration import Enumeration
from .xdr_float import Float, Double, Quadruple
from .xdr_sequence import FixedOpaque

class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1


# Not strictly necessary, because the above Boolean class definition
# will have added FALSE and TRUE to this module's global namespace.
# Explicitly setting them here allows static analyzers, such as typically
# used by an IDE for code completion, to recognize these values as part of the module.
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
    'FixedOpaque'
]
