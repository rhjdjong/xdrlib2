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


def test_optional_struct():
    opt_type = xdrlib.Optional(MyStruct)
    yes = opt_type(3, b'hello', 0)
    no = opt_type()
    assert isinstance(yes, opt_type)
    assert isinstance(yes, MyStruct)
    assert isinstance(no, opt_type)
    assert isinstance(no, xdrlib.Void)
    assert yes.a == 3
    assert yes.b == b'hello'
    assert yes.c == 0
    py = b'\0\0\0\x01' b'\0\0\0\x03' b'\0\0\0\x05hello\0\0\0' b'\0\0\0\0'
    pn = b'\0\0\0\0'
    assert yes.encode() == py
    assert no.encode() == pn
    nyes = opt_type.decode(py)
    assert nyes == yes
    assert nyes.encode() == py
    nno = opt_type.decode(pn)
    assert nno == no
    assert nno.encode() == pn


def test_struct_with_optional_field():
    m = xdrlib.Struct(a=xdrlib.Integer, b=xdrlib.Optional(xdrlib.Double), c=xdrlib.Boolean)
    m1 = m(1, 3.14, True)
    m2 = m(1, None, True)
    assert isinstance(m1.b, xdrlib.Optional)
    assert isinstance(m1.b, xdrlib.Double)
    assert m1.b == 3.14
    assert isinstance(m2.b, xdrlib.Optional)
    assert isinstance(m2.b, xdrlib.Void)
    assert m2.b == None
    p1 = b'\0\0\0\x01' + b'\0\0\0\x01' + xdrlib.Double(3.14).encode() + b'\0\0\0\x01'
    p2 = b'\0\0\0\x01' + b'\0\0\0\0' + b'\0\0\0\x01'
    assert m1.encode() == p1
    assert m2.encode() == p2
    n1 = m.decode(p1)
    n2 = m.decode(p2)
    assert n1 == m1
    assert n2 == m2
    assert n1.encode() == p1
    assert n2.encode() == p2


def test_struct_with_self_reference():
    with xdrlib.Struct() as SelfRefStruct:
        SelfRefStruct.x = xdrlib.Integer
        SelfRefStruct.link = xdrlib.Optional(SelfRefStruct)
    a = SelfRefStruct(x=3, link=None)
    b = SelfRefStruct(x=4, link=a)
    c = SelfRefStruct(x=5, link=b)
    pa = xdrlib.Integer(3).encode()
    pb = xdrlib.Integer(4).encode() + xdrlib.TRUE.encode() + pa
    pc = xdrlib.Integer(5).encode() + xdrlib.TRUE.encode() + pb
    assert a.encode() == pa
    assert b.encode() == pb
    assert c.encode() == pc
    na = SelfRefStruct.decode(pa)
    nb = SelfRefStruct.decode(pb)
    nc = SelfRefStruct.decode(pc)
    assert na == a
    assert nb == b
    assert nc == c
    assert na.encode() == pa
    assert nb.encode() == pb
    assert nc.encode() == pc
