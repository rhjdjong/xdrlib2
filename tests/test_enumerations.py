# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest

import xdrlib2 as xdrlib
import sys

current_module = sys.modules[__name__]


class Colors(xdrlib.Enumeration, RED=2, YELLOW=3, BLUE=5):
    pass


class Animals(xdrlib.Enumeration):
    CAT = 1
    DOG = 2
    HORSE = 5


def test_enumeration_with_subclass_arguments():
    assert issubclass(Colors, xdrlib.Enumeration)
    r = Colors.RED
    assert r == 2
    assert isinstance(r, Colors)
    y = Colors('YELLOW')
    assert isinstance(y, Colors)
    assert y == 3
    b = current_module.BLUE
    assert isinstance(b, Colors)
    assert b == 5
    assert Colors(3) == y


def test_enumeration_with_class_parameters():
    assert issubclass(Animals, xdrlib.Enumeration)
    c = Animals.CAT
    assert isinstance(c, Animals)
    assert c == 1
    d = Animals('DOG')
    assert isinstance(d, Animals)
    assert d == 2
    h = current_module.HORSE
    assert isinstance(h, Animals)
    assert h == 5
    assert Animals(1) == c


def test_predefined_boolean_values():
    assert issubclass(xdrlib.Boolean, xdrlib.Enumeration)
    assert isinstance(xdrlib.FALSE, xdrlib.Boolean)
    assert isinstance(xdrlib.TRUE, xdrlib.Boolean)
    assert xdrlib.FALSE == 0
    assert xdrlib.TRUE == 1


def test_instantiation_by_name():
    r = Colors('RED')
    assert r == Colors.RED
    assert r == 2
    assert isinstance(r, Colors)
    with pytest.raises(ValueError):
        Colors('Unknown')


def test_instantiation_by_value():
    b = Colors(5)
    assert b == Colors.BLUE
    assert b == 5
    assert isinstance(b, Colors)
    with pytest.raises(ValueError):
        Colors(10)


def test_cannot_intantiate_abstract_baseclass():
    with pytest.raises(NotImplementedError):
        xdrlib.Enumeration(0)


def test_cannot_subclass_concrete_baseclass():
    with pytest.raises(TypeError):
        class SubColor(Colors, white=10):
            pass


def test_cannot_create_additional_enumeration_identifiers():
    with pytest.raises(AttributeError):
        Colors.PURPLE = 15


def test_cannot_modify_enumeration_identifiers():
    with pytest.raises(AttributeError):
        Colors.RED = 4


def test_packing_of_enumerations():
    p = Colors.RED.encode()
    assert p == b'\0\0\0\x02'


def test_unpacking_of_enumerations():
    n = Colors.decode(b'\0\0\0\x03')
    assert isinstance(n, Colors)
    assert n == Colors.YELLOW


def test_unpacking_invalid_value_fails():
    with pytest.raises(ValueError):
        Colors.decode(b'\0\0\0\x04')
