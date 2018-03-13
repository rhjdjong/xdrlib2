# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest

import xdrlib2 as xdrlib

def test_void_instantiation():
    v1 = xdrlib.Void()
    v2 = xdrlib.Void(None)
    v3 = xdrlib.Void(v1)
    assert v1 == v2
    assert v1 == v3
    assert v2 == v3
    assert v1 == None
    assert v2 == None
    assert v3 == None

def test_void_encoding_and_decoding():
    v = xdrlib.Void()
    assert v.encode() == b''
    v2 = xdrlib.Void.decode(b'')
    assert isinstance(v2, xdrlib.Void)
    assert v2 == v
    assert v2.encode() == b''