# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest
import xdrlib2 as xdrlib


UnionWithDefault = xdrlib.Union.typedef('UnionWithDefault', kind=xdrlib.Integer)
UnionWithDefault.case(1, number=xdrlib.Integer)
UnionWithDefault.case(2, 3, text=xdrlib.String)
UnionWithDefault.case(4, flag=xdrlib.Boolean)
UnionWithDefault.default(xdrlib.Void)

class SimpleUnion(xdrlib.Union, discr=xdrlib.UnsignedInteger):
    pass
SimpleUnion.case(1, xdrlib.Void)
SimpleUnion.case(2, flag=xdrlib.Boolean)
SimpleUnion.case(3, text=xdrlib.String.typedef(size=10))
SimpleUnion.case(4, foo=xdrlib.UnsignedInteger)
SimpleUnion.default(whatever=xdrlib.FixedOpaque.typedef(size=4))


SimpleUnionFromEnum = xdrlib.Union.typedef('SimpleUnionFromEnum',
                                           discr=xdrlib.Enumeration.typedef(a=1, b=2, c=3))
SimpleUnionFromEnum.case(1, xdrlib.Void)
SimpleUnionFromEnum.case(2, number=xdrlib.Integer)
SimpleUnionFromEnum.case(3, logic=xdrlib.Boolean)
SimpleUnionFromEnum.default()


def test_example():
    assert issubclass(UnionWithDefault, xdrlib.Union)

    casetype = UnionWithDefault[1]
    assert issubclass(casetype, UnionWithDefault)
    assert issubclass(casetype, xdrlib.Integer)

    casevalue = casetype(5)
    assert isinstance(casevalue, casetype)
    assert isinstance(casevalue, UnionWithDefault)
    assert isinstance(casevalue, xdrlib.Integer)

    p = b'\0\0\0\x01' b'\0\0\0\x05'
    assert casevalue.encode() == p
    n = UnionWithDefault.decode(p)
    assert isinstance(n, casetype)
    assert isinstance(n, UnionWithDefault)
    assert isinstance(n, xdrlib.Integer)
    assert n == casevalue
    assert n.encode() == p


def test_invalid_switch_type():
    with pytest.raises(ValueError):
        casetype = UnionWithDefault['hallo']


def test_simple_union_invalid_initialization():
    with pytest.raises(ValueError):
        SimpleUnion[18](b'random value')
    with pytest.raises(ValueError):
        SimpleUnionFromEnum[5](b'some value')


def test_invalid_union_definition():
    with pytest.raises(ValueError):
        x = xdrlib.Union.typedef('x', discr=xdrlib.Integer)
        x.case(1, a=xdrlib.Boolean)
        x.case(2, a=xdrlib.Float)
        x.default(c=xdrlib.Hyper)
    with pytest.raises(ValueError):
        x = xdrlib.Union.typedef('x', a=xdrlib.Integer)
        x.case(1, a=xdrlib.Boolean)
        x.case(2, b=xdrlib.Float)
        x.default()


def test_simple_union_from_enum():
    a = SimpleUnionFromEnum[1](None)
    b = SimpleUnionFromEnum[2](12345)
    c = SimpleUnionFromEnum[3](True)
    assert a.switch == 1
    assert a == None
    assert isinstance(a, SimpleUnionFromEnum)
    assert isinstance(a, xdrlib.Void)
    assert b.switch == 2
    assert b == 12345
    assert isinstance(b, SimpleUnionFromEnum)
    assert isinstance(b, xdrlib.Integer)
    assert c.switch == 3
    assert c == True
    assert isinstance(c, SimpleUnionFromEnum)
    assert isinstance(c, xdrlib.Boolean)

    pa = a.encode()
    pb = b.encode()
    pc = c.encode()
    assert pa == xdrlib.Integer(1).encode()
    assert pb == xdrlib.Integer(2).encode() + xdrlib.Integer(12345).encode()
    assert pc == xdrlib.Integer(3).encode() + xdrlib.TRUE.encode()

    na = SimpleUnionFromEnum.decode(pa)
    nb = SimpleUnionFromEnum.decode(pb)
    nc = SimpleUnionFromEnum.decode(pc)

    assert na == a
    assert nb == b
    assert nc == c


def test_simple_union_1():
    u = SimpleUnion[1]()
    assert u.switch == 1
    assert u == None
    assert isinstance(u, SimpleUnion)
    assert isinstance(u, xdrlib.Void)

    bp = u.encode()
    assert bp == xdrlib.Integer(1).encode()
    nu = SimpleUnion.decode(bp)
    assert nu == u



def test_simple_union_3():
    s = b'hello'
    u = SimpleUnion[3](s)
    assert u.switch == 3
    assert u == s
    assert isinstance(u, SimpleUnion)
    assert isinstance(u, xdrlib.String)

    bp = u.encode()
    assert bp == xdrlib.Integer(3).encode() + xdrlib.String.typedef(size=10)(s).encode()
    nu = SimpleUnion.decode(bp)
    assert nu == u


def test_simple_union_4():
    u = SimpleUnion[4](13)
    assert u.switch == 4
    assert u == 13
    assert isinstance(u, SimpleUnion)
    assert isinstance(u, xdrlib.UnsignedInteger)

    bp = u.encode()
    assert bp == xdrlib.Integer(4).encode() + xdrlib.UnsignedInteger(13).encode()
    nu = SimpleUnion.decode(bp)
    assert nu == u


def test_simple_union_default():
    u = SimpleUnion[255](b'dumb')
    assert u.switch == 255
    assert u == b'dumb'
    assert isinstance(u, SimpleUnion)
    assert isinstance(u, xdrlib.FixedOpaque)

    bp = u.encode()
    assert bp == xdrlib.Integer(255).encode() + b'dumb'
    nu = SimpleUnion.decode(bp)
    assert nu == u


def test_union_subclassing_fails_for_invalid_swith_type():
    with pytest.raises(TypeError):
        xdrlib.Union(discr=xdrlib.Hyper)


def test_optional_union():
    OptUnion = xdrlib.Optional(SimpleUnion)
    y1 = OptUnion[1](None)
    y2 = OptUnion[2](True)
    y3 = OptUnion[3](b'hallo')
    y4 = OptUnion[4](13)
    y5 = OptUnion[5](b'dumb')
    no = OptUnion()

