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


def test_struct_encoding_and_decoding():
    m = MyStruct(3, b'hello', 0)
    packed = b'\0\0\0\x03' b'\0\0\0\x05hello\0\0\0' b'\0\0\0\0'
    assert m.encode() == packed
    n = MyStruct.decode(packed)
    assert n == m
    assert n.encode() == packed


def test_struct_field_modification():
    n = MyOtherStruct(y=13, x=True)
    assert n.x == True
    assert n.y == 13
    n.y = 4
    assert n.y == 4
    packed = b'\0\0\0\x01' b'\0\0\0\0\0\0\0\x04'
    assert n.encode() == packed


def test_struct_field_deletion_fails():
    m = MyStruct(3, b'hello', 0)
    with pytest.raises(AttributeError):
        del m.x


def test_struct_initialization_fails_with_too_many_argument():
    with pytest.raises(ValueError):
        MyStruct(4, b'test', 'YES', 'extra')


def test_struct_initialization_fails_with_wrong_argument_types():
    with pytest.raises(ValueError):
        MyStruct(b'hello', 4, 1)


def test_struct_field_modification_fails_with_wrong_argument_type():
    m = MyStruct(3, b'hello', 0)
    with pytest.raises((ValueError, TypeError)):
        m.c = 3
