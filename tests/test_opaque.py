# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import xdrlib2 as xdrlib
import pytest


class MyFixedOpaque(xdrlib.FixedOpaque, size=10):
    pass


def test_fixed_length_opaque_through_argument():
    byte_seq = b'0123456789'
    x = MyFixedOpaque(byte_seq)
    assert isinstance(x, MyFixedOpaque)
    assert x == byte_seq
    p = x.encode()
    assert p == byte_seq + b'\0\0'
    n = MyFixedOpaque.decode(p)
    assert isinstance(n, MyFixedOpaque)
    assert n == x
    assert n.encode() == p


def test_default_instantiation_has_all_zero_bytes():
    x = MyFixedOpaque()
    assert isinstance(x, MyFixedOpaque)
    assert x == b'\0' * 10


def test_fixed_length_instantiation_fails_with_wrong_sized_argument():
    with pytest.raises(ValueError):
        MyFixedOpaque(b'too short')
    with pytest.raises(ValueError):
        MyFixedOpaque(b'way too long')



