# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import xdrlib2 as xdrlib
import pytest


class MyFixedOpaque(xdrlib.FixedOpaque, maxsize=10):
    pass


class MyVarOpaque(xdrlib.VarOpaque):
    maxsize = 10


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


def test_var_length_opaque_through_argument():
    byte_seq = b'0123456789'
    x = MyVarOpaque(byte_seq)
    assert isinstance(x, MyVarOpaque)
    assert x == byte_seq
    p = x.encode()
    assert p == b'\0\0\0\x0a' + byte_seq + b'\0\0'
    n = MyVarOpaque.decode(p)
    assert isinstance(n, MyVarOpaque)
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


def test_subclassing_with_size_failse():
    with pytest.raises(TypeError):
        class InvalidSubClass(MyFixedOpaque, maxsize=5):
            pass


def test_subclassing_without_changes_works():
    class Other(MyFixedOpaque):
        pass
    assert Other.maxsize() == MyFixedOpaque.maxsize()


def test_modifying_size_fails():
    with pytest.raises(AttributeError):
        MyFixedOpaque._maxsize = 5
