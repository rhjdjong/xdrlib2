# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest
import xdrlib2 as xdrlib


ArmString = xdrlib.String.typedef(size=10)
ArmOpaque = xdrlib.FixedOpaque.typedef(size=4)
SwitchEnum = xdrlib.Enumeration.typedef(a=1, b=2, c=3)


class SimpleUnion(xdrlib.Union, discr=xdrlib.UnsignedInteger):
    pass
SimpleUnion.case(1, xdrlib.Void)
SimpleUnion.case(2, flag=xdrlib.Boolean)
SimpleUnion.case(3, text=ArmString)
SimpleUnion.case(4, foo=xdrlib.UnsignedInteger)
SimpleUnion.default(whatever=ArmOpaque)


with xdrlib.Union.typedef('SimpleUnionFromEnum', discr=SwitchEnum) as SimpleUnionFromEnum:
    SimpleUnionFromEnum.case(1, xdrlib.Void)
    SimpleUnionFromEnum.case(2, number=xdrlib.Integer)
    SimpleUnionFromEnum.case(3, logic=xdrlib.Boolean)


UnfinishedUnion = xdrlib.Union.typedef('UnfinishedUnion', kind=xdrlib.Integer)
UnfinishedUnion.case(3, arm=xdrlib.Boolean)


@pytest.mark.parametrize('uniontype,switch,switchtype,arg,armtype,armname', [
    (SimpleUnion, 1, xdrlib.UnsignedInteger, None, xdrlib.Void, None),
    (SimpleUnion, 2, xdrlib.UnsignedInteger, True, xdrlib.Boolean, 'flag'),
    (SimpleUnion, 3, xdrlib.UnsignedInteger, b'hello', ArmString, 'text'),
    (SimpleUnion, 4, xdrlib.UnsignedInteger, 13, xdrlib.UnsignedInteger, 'foo'),
    (SimpleUnion, 5, xdrlib.UnsignedInteger, b'dumb', ArmOpaque, 'whatever'),
    (SimpleUnionFromEnum, 1, SwitchEnum, None, xdrlib.Void, None),
    (SimpleUnionFromEnum, 2, SwitchEnum, 13, xdrlib.Integer, 'number'),
    (SimpleUnionFromEnum, 3, SwitchEnum, True, xdrlib.Boolean, 'logic'),
    (SimpleUnionFromEnum, SwitchEnum.a, SwitchEnum, None, xdrlib.Void, None),
    (SimpleUnionFromEnum, SwitchEnum.b, SwitchEnum, 13, xdrlib.Integer, 'number'),
    (SimpleUnionFromEnum, SwitchEnum.c, SwitchEnum, False, xdrlib.Boolean, 'logic')
])
def test_union_instantiation(uniontype, switch, switchtype, arg, armtype, armname):
    x = uniontype(switch, arg)
    assert isinstance(x, uniontype)
    assert isinstance(x, armtype)
    assert x.switch == switch
    assert x == arg

    p = xdrlib.encode(switchtype(switch)) + xdrlib.encode(armtype(arg))
    assert xdrlib.encode(x) == p
    y = xdrlib.decode(uniontype, p)
    assert y == x
    assert xdrlib.encode(y) == p


def test_union_attributes():
    assert SimpleUnion.switch_name == 'discr'
    x = SimpleUnion(3, b'hello')
    assert x.switch == 3
    assert x.case == 'text'


@pytest.mark.parametrize('uniontype,switch,switchtype,arg,armtype,armname', [
    (SimpleUnion, 1, xdrlib.UnsignedInteger, None, xdrlib.Void, None),
    (SimpleUnion, 2, xdrlib.UnsignedInteger, True, xdrlib.Boolean, 'flag'),
    (SimpleUnion, 3, xdrlib.UnsignedInteger, b'hello', ArmString, 'text'),
    (SimpleUnion, 4, xdrlib.UnsignedInteger, 13, xdrlib.UnsignedInteger, 'foo'),
    (SimpleUnion, 5, xdrlib.UnsignedInteger, b'dumb', ArmOpaque, 'whatever'),
    (SimpleUnionFromEnum, 1, SwitchEnum, None, xdrlib.Void, None),
    (SimpleUnionFromEnum, 2, SwitchEnum, 13, xdrlib.Integer, 'number'),
    (SimpleUnionFromEnum, 3, SwitchEnum, True, xdrlib.Boolean, 'logic'),
    (SimpleUnionFromEnum, SwitchEnum.a, SwitchEnum, None, xdrlib.Void, None),
    (SimpleUnionFromEnum, SwitchEnum.b, SwitchEnum, 13, xdrlib.Integer, 'number'),
    (SimpleUnionFromEnum, SwitchEnum.c, SwitchEnum, False, xdrlib.Boolean, 'logic')
])
def test_union_repr_and_str_format(uniontype, switch, switchtype, arg, armtype, armname):
    item = uniontype(switch, arg)
    if armname:
        expected_arm_repr = f"{armname:s}={armtype(arg)!s}"
    else:
        expected_arm_repr = f"{armtype(arg)!s}"
    expected_repr = f"{uniontype.__name__:s}[{item.switch!s}]({expected_arm_repr:s})"
    expected_str = f"{{{item.switch!s}:{armtype(arg)!s}}}"
    assert repr(item) == expected_repr
    assert str(item) == expected_str


def test_incomplete_union_instantiation_fails():
    with pytest.raises(NotImplementedError):
        UnfinishedUnion(3, True)


def test_union_instantiation_with_invalid_switch_type_fails():
    with pytest.raises((ValueError, TypeError)):
        SimpleUnion('hallo', 3)


def test_union_instantiation_with_invalid_switch_value_fails():
    with pytest.raises(ValueError):
        SimpleUnionFromEnum(4, 13)


def test_union_initialization_with_invalid_arm_value_fails():
    with pytest.raises(ValueError):
        SimpleUnion(2, b'random value')


@pytest.mark.parametrize('type', [
    xdrlib.String,
    xdrlib.Enumeration,
    xdrlib.VarArray,
    xdrlib.Union
])
def test_union_creation_with_abstract_arm_type_fails(type):
    with pytest.raises((ValueError, TypeError)):
        UnfinishedUnion.case(1, invalid=type)


def test_union_definition_with_duplicate_arm_name_fails():
    with xdrlib.Union.typedef('MyUnion', discr=xdrlib.Integer) as MyUnion:
        MyUnion.case(1, a=xdrlib.Boolean)
        with pytest.raises(ValueError):
            MyUnion.case(2, a=xdrlib.Float)


def test_union_definition_with_arm_name_equal_to_switch_name_fails():
    with xdrlib.Union.typedef('MyUnion', a=xdrlib.Integer) as MyUnion:
        with pytest.raises(ValueError):
            MyUnion.case(1, a=xdrlib.Boolean)


def test_union_definition_with_duplicate_switch_values_fails():
    with xdrlib.Union.typedef('MyUnion', a=xdrlib.Integer) as MyUnion:
        MyUnion.case(1, 2, 3, b=xdrlib.Boolean)
        with pytest.raises((ValueError, TypeError)):
            MyUnion.case(2, c=xdrlib.Integer)




def test_union_creation_with_optional_recursion_works():
    UnfinishedUnion.case(1, opt_recurse=xdrlib.Optional(UnfinishedUnion))


OptUnion = xdrlib.Optional(SimpleUnion)


@pytest.mark.parametrize('present,switch,arg,argtype', [
    (True, 1, None, xdrlib.Void),
    (True, 2, True, xdrlib.Boolean),
    (True, 3, b'hallo', ArmString),
    (True, 4, 13, xdrlib.UnsignedInteger),
    (True, 5, b'dumb', ArmOpaque),
    (False, None, None, None)
])
def test_optional_union(present, switch, arg, argtype):
    if present:
        y = OptUnion(switch, arg)
        assert isinstance(y, argtype)
        assert y == arg
        if argtype != xdrlib.Void:
            assert not isinstance(y, xdrlib.Void)
        p = xdrlib.encode(xdrlib.TRUE) + xdrlib.encode(xdrlib.Integer(switch)) + xdrlib.encode(argtype(arg))
    else:
        y = OptUnion(None)
        assert isinstance(y, xdrlib.Void)
        p = xdrlib.encode(xdrlib.FALSE)
    assert xdrlib.encode(y) == p
    ny = xdrlib.decode(OptUnion, p)
    assert ny == y
    assert xdrlib.encode(ny) == p


def test_self_refererential_union():
    with xdrlib.Union.typedef('SelfRefUnion', number=xdrlib.Integer) as SelfRefUnion:
        SelfRefUnion.case(1, a=xdrlib.Integer)
        SelfRefUnion.case(2, link=xdrlib.Optional(SelfRefUnion))

    ua = SelfRefUnion(1, 13)
    ub = SelfRefUnion(2, None)
    uc = SelfRefUnion(2, ua)
    pa = b'\0\0\0\x01' b'\0\0\0\x0d'
    pb = b'\0\0\0\x02' b'\0\0\0\0'
    pc = b'\0\0\0\x02' b'\0\0\0\x01' b'\0\0\0\x01' b'\0\0\0\x0d'
    assert xdrlib.encode(ua) == pa
    ua2 = xdrlib.decode(SelfRefUnion, pa)
    assert ua2 == ua
    assert xdrlib.encode(ua2) == pa
    assert xdrlib.encode(ub) == pb
    ub2 = xdrlib.decode(SelfRefUnion, pb)
    assert ub2 == ub
    assert xdrlib.encode(ub2) == pb
    assert xdrlib.encode(uc) == pc
    uc2 = xdrlib.decode(SelfRefUnion, pc)
    assert uc2 == uc
    assert xdrlib.encode(uc2) == pc
