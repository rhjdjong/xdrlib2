# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest
import xdrlib2 as xdrlib


def test_default_instantiation():
    assert xdrlib.Int32() == 0
    assert xdrlib.Int32u() == 0
    assert xdrlib.Int64() == 0
    assert xdrlib.Int64u() == 0


@pytest.mark.parametrize("xdrtype,values", [
    (xdrlib.Int32, [-2 ** 31, -123456, -1, 0, 1, 34567, 2 ** 31 - 1]),
    (xdrlib.Int32u, [0, 1, 345678, 2 ** 32 - 1]),
    (xdrlib.Int64, [-2 ** 63, -2 ** 31 - 1, -123456, -1, 0, 1, 345678, 2 ** 31, 2 ** 63 - 1]),
    (xdrlib.Int64u, [0, 1, 2 ** 32, 2 ** 64 - 1])
])
def test_valid_values(xdrtype, values):
    for v in values:
        x = xdrtype(v)
        assert x == v
        assert isinstance(x, xdrtype)


@pytest.mark.parametrize("xdrtype,values", [
    (xdrlib.Int32, [-2 ** 31 - 1, 2 ** 31]),
    (xdrlib.Int32u, [-1, 2 ** 32]),
    (xdrlib.Int64, [-2 ** 63 - 1, 2 ** 63]),
    (xdrlib.Int64u, [-1, 2 ** 64])
])
def test_invalid_values(xdrtype, values):
    for v in values:
        with pytest.raises(ValueError):
            xdrtype(v)


@pytest.mark.parametrize("xdrtype,values,packed", [
    (xdrlib.Int32, [-2 ** 31, -1, 0, 1, 2 ** 31 - 1],
     [b'\x80\0\0\0', b'\xff\xff\xff\xff', b'\0\0\0\0', b'\0\0\0\x01', b'\x7f\xff\xff\xff']),
    (xdrlib.Int32u, [0, 1, 2 ** 31 - 1, 2 ** 31, 2 ** 32 - 1],
     [b'\0\0\0\0', b'\0\0\0\x01', b'\x7f\xff\xff\xff', b'\x80\0\0\0', b'\xff\xff\xff\xff']),
    (xdrlib.Int64, [-2 ** 63, -1, 0, 1, 2 ** 63 - 1],
     [b'\x80\0\0\0\0\0\0\0', b'\xff\xff\xff\xff\xff\xff\xff\xff', b'\0\0\0\0\0\0\0\0',
      b'\0\0\0\0\0\0\0\x01', b'\x7f\xff\xff\xff\xff\xff\xff\xff']),
    (xdrlib.Int64u, [0, 1, 2 ** 63 - 1, 2 ** 63, 2 ** 64 - 1],
     [b'\0\0\0\0\0\0\0\0', b'\0\0\0\0\0\0\0\x01', b'\x7f\xff\xff\xff\xff\xff\xff\xff',
      b'\x80\0\0\0\0\0\0\0', b'\xff\xff\xff\xff\xff\xff\xff\xff'])
])
def test_packing_and_unpacking(xdrtype, values, packed):
    for v, p in zip(values, packed):
        assert xdrtype(v).encode() == p
        x = xdrtype.decode(p)
        assert x == v
        assert isinstance(x, xdrtype)
