# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest

import xdrlib2 as xdrlib
import sys

current_module = sys.modules[__name__]


class Colors(xdrlib.Enumeration, RED=2, YELLOW=3, BLUE=5):
    pass


def test_new_enumeration():
    assert issubclass(Colors, xdrlib.Enumeration)
    assert Colors.RED == 2
    assert current_module.BLUE == 5


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
