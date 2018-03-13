# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest

import xdrlib2 as xdrlib

class MyStruct(xdrlib.Struct):
    a = xdrlib.Integer
    b = xdrlib.String.typedef('B', size=10)
    c = xdrlib.Enumeration.typedef('C', NO=0, YES=1)


MyOtherStruct = xdrlib.Struct.typedef(
    'MyOtherStruct',
    x = xdrlib.Boolean,
    y = xdrlib.Hyper
)


def test_struct_initialization():
    m = MyStruct(c='YES')
    assert m.a == 0
    assert isinstance(m.a, xdrlib.Integer)
    assert m.b == b''
    assert isinstance(m.b, xdrlib.String)
    assert m.c == 1
    assert isinstance(m.c, xdrlib.Enumeration)

    m = MyOtherStruct(y=3, x=xdrlib.TRUE)
    assert m.x == xdrlib.TRUE
    assert isinstance(m.x, xdrlib.Boolean)
    assert m.y == 3
    assert isinstance(m.y, xdrlib.Hyper)

