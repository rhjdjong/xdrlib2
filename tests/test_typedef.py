# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest
import xdrlib2 as xdrlib

import sys
current_module = sys.modules[__name__]


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Integer,
    xdrlib.UnsignedInteger,
    xdrlib.Hyper,
    xdrlib.UnsignedHyper,
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_typedef_from_atomic_types(xdrtype):
    new_type = xdrtype.typedef()
    assert issubclass(new_type, xdrtype)
    with pytest.raises(AttributeError):
        new_type.foo = 0


def test_typedef_for_enumeration():
    new_enum_type = xdrlib.Enumeration.typedef(ONE=1, TWO=2, THREE=3)
    assert new_enum_type.ONE == 1
    assert new_enum_type('TWO') == 2
    assert new_enum_type(3) == new_enum_type.THREE


@pytest.mark.parametrize('xdrtype', [
    xdrlib.FixedOpaque,
    xdrlib.VarOpaque,
    xdrlib.String
])
def test_typedef_for_opaque_and_string(xdrtype):
    new_type = xdrtype.typedef(size=20)
    assert issubclass(new_type, xdrtype)
    assert new_type.size == 20