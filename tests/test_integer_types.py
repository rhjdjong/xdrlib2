# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest
import xdrlib2 as xdrlib
from xdrlib2.xdr_integer import XdrInteger


@pytest.mark.parametrize("xdrtype", [
    xdrlib.Integer,
    xdrlib.UnsignedInteger,
    xdrlib.Hyper,
    xdrlib.UnsignedHyper
])
def test_default_instantiation(xdrtype):
    assert xdrtype() == 0


@pytest.mark.parametrize("xdrtype,min,max,signed,packed_size", [
    (xdrlib.Integer, -2**31, 2**31, True, 4),
    (xdrlib.UnsignedInteger, 0, 2**32, False, 4),
    (xdrlib.Hyper, -2**63, 2**63, True, 8),
    (xdrlib.UnsignedHyper, 0, 2**64, False, 8),
])
def test_integer_type_parameters(xdrtype, min, max, signed, packed_size):
    assert xdrtype.min == min
    assert xdrtype.max == max
    assert xdrtype.signed == signed
    assert xdrtype.packed_size == packed_size


@pytest.mark.parametrize("xdrtype", [
    xdrlib.Integer,
    xdrlib.UnsignedInteger,
    xdrlib.Hyper,
    xdrlib.UnsignedHyper
])
def test_parameter_modification_fails_for_final_types(xdrtype):
    with pytest.raises(AttributeError):
        xdrtype.min = 13
    with pytest.raises(AttributeError):
        del xdrtype.max


@pytest.mark.parametrize("xdrtype,values", [
    (xdrlib.Integer, [-2 ** 31, -123456, -1, 0, 1, 34567, 2 ** 31 - 1]),
    (xdrlib.UnsignedInteger, [0, 1, 345678, 2 ** 32 - 1]),
    (xdrlib.Hyper, [-2 ** 63, -2 ** 31 - 1, -123456, -1, 0, 1, 345678, 2 ** 31, 2 ** 63 - 1]),
    (xdrlib.UnsignedHyper, [0, 1, 2 ** 32, 2 ** 64 - 1])
])
def test_valid_values(xdrtype, values):
    for v in values:
        x = xdrtype(v)
        assert x == v
        assert isinstance(x, xdrtype)


@pytest.mark.parametrize("xdrtype,values", [
    (xdrlib.Integer, [-2 ** 31 - 1, 2 ** 31]),
    (xdrlib.UnsignedInteger, [-1, 2 ** 32]),
    (xdrlib.Hyper, [-2 ** 63 - 1, 2 ** 63]),
    (xdrlib.UnsignedHyper, [-1, 2 ** 64])
])
def test_invalid_values(xdrtype, values):
    for v in values:
        with pytest.raises(OverflowError):
            xdrtype(v)


@pytest.mark.parametrize("xdrtype,values,packed", [
    (xdrlib.Integer, [-2 ** 31, -1, 0, 1, 2 ** 31 - 1],
     [b'\x80\0\0\0', b'\xff\xff\xff\xff', b'\0\0\0\0', b'\0\0\0\x01', b'\x7f\xff\xff\xff']),
    (xdrlib.UnsignedInteger, [0, 1, 2 ** 31 - 1, 2 ** 31, 2 ** 32 - 1],
     [b'\0\0\0\0', b'\0\0\0\x01', b'\x7f\xff\xff\xff', b'\x80\0\0\0', b'\xff\xff\xff\xff']),
    (xdrlib.Hyper, [-2 ** 63, -1, 0, 1, 2 ** 63 - 1],
     [b'\x80\0\0\0\0\0\0\0', b'\xff\xff\xff\xff\xff\xff\xff\xff', b'\0\0\0\0\0\0\0\0',
      b'\0\0\0\0\0\0\0\x01', b'\x7f\xff\xff\xff\xff\xff\xff\xff']),
    (xdrlib.UnsignedHyper, [0, 1, 2 ** 63 - 1, 2 ** 63, 2 ** 64 - 1],
     [b'\0\0\0\0\0\0\0\0', b'\0\0\0\0\0\0\0\x01', b'\x7f\xff\xff\xff\xff\xff\xff\xff',
      b'\x80\0\0\0\0\0\0\0', b'\xff\xff\xff\xff\xff\xff\xff\xff'])
])
def test_packing_and_unpacking(xdrtype, values, packed):
    for v, p in zip(values, packed):
        x = xdrtype(v)
        assert x == v
        assert xdrlib.encode(x) == p
        y = xdrlib.decode(xdrtype, p)
        assert x == y
        assert isinstance(y, xdrtype)
        assert xdrlib.encode(y) == p


def test_anonymous_subclass():
    i_bit = XdrInteger.typedef(min=0, max=2)
    assert issubclass(i_bit, XdrInteger)
    assert issubclass(i_bit, int)
    zero = i_bit(0)
    one = i_bit(1)
    assert isinstance(zero, i_bit)
    assert isinstance(one, i_bit)
    assert zero == 0
    assert one == 1
    assert xdrlib.encode(zero) == b'\0\0\0\0'
    assert xdrlib.encode(one) == b'\x01\0\0\0'
    new_zero = xdrlib.decode(i_bit, b'\0\0\0\0')
    new_one = xdrlib.decode(i_bit, b'\x01\0\0\0')
    assert new_zero == zero
    assert new_one == one
    assert isinstance(new_zero, i_bit)
    assert isinstance(new_one, i_bit)
    assert xdrlib.encode(new_zero) == b'\0\0\0\0'
    assert xdrlib.encode(new_one) == b'\x01\0\0\0'

def test_anonymous_subclass_error_situations():
    i_bit = XdrInteger.typedef(min=0, max=2)
    with pytest.raises(OverflowError):
        i_bit(2)
    with pytest.raises(TypeError):
        xdrlib.Integer.typedef(min=0, max=2)
    with pytest.raises(TypeError):
        XdrInteger.typedef(min=3)
    with pytest.raises(TypeError):
        XdrInteger.typedef(min=3, max=5, extra=7)
    with pytest.raises(ValueError):
        XdrInteger.typedef(min=2, max=0)


