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


@pytest.mark.parametrize("enumtype,intvalue,enumvalue", [
    (Colors, 2, RED),
    (Colors, 3, YELLOW),
    (Colors, 5, BLUE),
    (Animals, 1, CAT),
    (Animals, 2, DOG),
    (Animals, 5, HORSE)
])
def test_enumeration_values_are_singletons(enumtype, intvalue, enumvalue):
    assert enumtype(intvalue) == enumvalue


@pytest.mark.parametrize("enumtype,default", [
    (Colors, Colors.RED),
    (Animals, Animals.CAT)
])
def test_default_enumeration_value_is_first_defined_value(enumtype, default):
    assert enumtype() == default


@pytest.mark.parametrize("enumtype,values", [
    (Colors, [Colors.RED, Colors.YELLOW, Colors.BLUE]),
    (Animals, [Animals.CAT, Animals.DOG, Animals.HORSE])
])
def test_enumeration_values_are_iterable(enumtype, values):
    for i, v in zip(enumtype, values):
        assert i == v


@pytest.mark.parametrize("enumtype,name,value", [
    (Colors, 'BLUE', BLUE),
    (Animals, 'DOG', DOG)
])
def test_enumeration_type_can_be_indexed(enumtype, name, value):
    assert enumtype[name] == value


def test_class_hierarchy():
    assert issubclass(Colors, xdrlib.Enumeration)
    assert issubclass(Animals, xdrlib.Enumeration)


def test_enumeration_values_are_instances_of_their_class():
    assert isinstance(RED, Colors)
    assert isinstance(DOG, Animals)


def test_enumeration_values_are_integers():
    assert Colors.RED == 2
    assert Colors['YELLOW'] == 3
    assert BLUE == 5
    assert Animals.CAT == 1
    assert Animals['DOG'] == 2
    assert HORSE == 5


@pytest.mark.parametrize("value,str_rep", [
    (Colors.RED, 'RED(2)'),
    (Animals.HORSE, 'HORSE(5)')
])
def test_string_representation_for_enumeration_values(value, str_rep):
    assert str(value) == str_rep


def test_predefined_boolean_values():
    assert issubclass(xdrlib.Boolean, xdrlib.Enumeration)
    assert isinstance(xdrlib.FALSE, xdrlib.Boolean)
    assert isinstance(xdrlib.TRUE, xdrlib.Boolean)
    assert xdrlib.FALSE == 0
    assert xdrlib.TRUE == 1


def test_unknown_enum_name_raises_value_error():
    with pytest.raises(AttributeError):
        Colors['Unknown']


def test_unknown_enum_value_raises_value_error():
    with pytest.raises(ValueError):
        Animals(10)


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
    with pytest.raises(TypeError):
        class InvalidEnum(xdrlib.Enumeration, OK_NAME=1, EXISTING_VALUE=2):
            EXISTING_VALUE = 3


# def test_cannot_create_enumeration_with_python_keywords():
#     weird_enum = xdrlib.Enumeration.typedef('Weird', **{'id': 1, 'if': 2, 'while': 3})
#     assert weird_enum.id == 1
#     assert weird_enum('if') == 2


def test_packing_of_enumerations():
    p = xdrlib.encode(Colors.RED)
    assert p == b'\0\0\0\x02'


def test_unpacking_of_enumerations():
    n = xdrlib.decode(Colors, b'\0\0\0\x03')
    assert isinstance(n, Colors)
    assert n == Colors.YELLOW


def test_unpacking_invalid_value_fails():
    with pytest.raises(ValueError):
        xdrlib.decode(Colors, b'\0\0\0\x04')


def test_boolean():
    assert xdrlib.TRUE == True
    assert xdrlib.FALSE == False
    assert xdrlib.Boolean(True) == xdrlib.TRUE
    assert xdrlib.Boolean(False) == xdrlib.FALSE


def test_optional_enumeration():
    OptColor = xdrlib.Optional(Colors)
    n = OptColor(None)
    assert isinstance(n, OptColor)
    assert isinstance(n, xdrlib.Void)
    assert n == None
    pn = b'\0\0\0\0'
    assert xdrlib.encode(n) == pn
    n1 =  xdrlib.decode(OptColor, pn)
    assert n1 == n
    assert xdrlib.encode(n1) == pn

    r = OptColor(2)
    assert isinstance(r, OptColor)
    assert isinstance(r, Colors)
    assert r == Colors.RED
    pr = b'\0\0\0\x01' b'\0\0\0\x02'
    assert xdrlib.encode(r) == pr
    r1 = xdrlib.decode(OptColor, pr)
    assert r1 == r
    assert xdrlib.encode(r1) == pr

    y = OptColor['YELLOW']
    assert isinstance(y, OptColor)
    assert isinstance(y, Colors)
    assert y == Colors.YELLOW
    py = b'\0\0\0\x01' b'\0\0\0\x03'
    assert xdrlib.encode(y) == py
    y1 = xdrlib.decode(OptColor, py)
    assert y1 == y
    assert xdrlib.encode(y1) == py

    b = OptColor.BLUE
    assert isinstance(b, OptColor)
    assert isinstance(b, Colors)
    assert b == Colors.BLUE
    pb = b'\0\0\0\x01' b'\0\0\0\x05'
    assert xdrlib.encode(b) == pb
    b1 = xdrlib.decode(OptColor, pb)
    assert b1 == b
    assert xdrlib.encode(b1) == pb

