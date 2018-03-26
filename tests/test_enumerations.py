# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest

import xdrlib2 as xdrlib
import sys

current_module = sys.modules[__name__]


Colors = xdrlib.Enumeration.typedef('Colors', RED=2, YELLOW=3, BLUE=5)

RED = Colors.RED
YELLOW = Colors.YELLOW
BLUE = Colors.BLUE


class Animals(xdrlib.Enumeration, HORSE=5):
    CAT = 1
    DOG = 2

CAT = Animals.CAT
DOG = Animals.DOG
HORSE = Animals.HORSE


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
        class SubColor(Colors, WHITE=10):
            pass


def test_cannot_create_additional_enumeration_identifiers():
    with pytest.raises(AttributeError):
        Colors.PURPLE = 15


def test_cannot_modify_enumeration_identifiers():
    with pytest.raises(AttributeError):
        Colors.RED = 4


def test_cannot_delete_enumeration_identifiers():
    with pytest.raises(AttributeError):
        del Colors.BLUE


def test_cannot_create_enumeration_that_overrides_module_attribute():
    with pytest.raises(ValueError):
        class InvalidEnum(xdrlib.Enumeration, OK_NAME=1, EXISTING_VALUE=2):
            EXISTING_VALUE = 3


def test_can_create_enumeration_with_python_keywords():
    weird_enum = xdrlib.Enumeration.typedef('Weird', **{'id': 1, 'if': 2, 'while': 3})
    assert weird_enum.id == 1
    assert weird_enum('if') == 2


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


def test_boolean():
    assert xdrlib.TRUE == True
    assert xdrlib.FALSE == False
    assert xdrlib.Boolean(True) == xdrlib.TRUE
    assert xdrlib.Boolean(False) == xdrlib.FALSE


def test_anonymous_enumeration():
    anon = xdrlib.Enumeration(XX=3, YY=4)
    assert issubclass(anon, xdrlib.Enumeration)
    xx = anon.XX
    assert isinstance(xx, anon)
    assert xx == 3
    assert xx.encode() == b'\0\0\0\x03'
    assert anon.decode(b'\0\0\0\x04') == anon.YY


def test_optional_enumeration():
    OptColor = xdrlib.Optional(Colors)
    n = OptColor()
    assert isinstance(n, OptColor)
    assert isinstance(n, xdrlib.Void)
    assert n == None
    pn = b'\0\0\0\0'
    assert n.encode() == pn
    n1 =  OptColor.decode(pn)
    assert n1 == n
    assert n1.encode() == pn

    r = OptColor(2)
    assert isinstance(r, OptColor)
    assert isinstance(r, Colors)
    assert r == Colors.RED
    pr = b'\0\0\0\x01' b'\0\0\0\x02'
    assert r.encode() == pr
    r1 = OptColor.decode(pr)
    assert r1 == r
    assert r1.encode() == pr

    y = OptColor('YELLOW')
    assert isinstance(y, OptColor)
    assert isinstance(y, Colors)
    assert y == Colors.YELLOW
    py = b'\0\0\0\x01' b'\0\0\0\x03'
    assert y.encode() == py
    y1 = OptColor.decode(py)
    assert y1 == y
    assert y1.encode() == py

    b = OptColor(Colors.BLUE)
    assert isinstance(b, OptColor)
    assert isinstance(b, Colors)
    assert b == Colors.BLUE
    pb = b'\0\0\0\x01' b'\0\0\0\x05'
    assert b.encode() == pb
    b1 = OptColor.decode(pb)
    assert b1 == b
    assert b1.encode() == pb

