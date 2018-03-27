# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest
import xdrlib2 as xdrlib


optional_integer_type = xdrlib.Optional(xdrlib.Integer)


def test_optional_class_is_subclass_of_Optional():
    assert issubclass(optional_integer_type, xdrlib.Optional)


def test_optional_class_name_is_by_default_derived_from_original_class():
    assert optional_integer_type.__name__ == '*Integer'


def test_optional_integer_is_not_a_subtype_of_integer():
    assert not issubclass(optional_integer_type, xdrlib.Integer)


@pytest.mark.parametrize('xdrtype', [
    optional_integer_type,  # direct instantiation
    # optional_integer_type(3).__class__,  # through the class of a present value
    # optional_integer_type(None).__class__, # through the class of an absent value
])
def test_present_optional_value_instantiation(xdrtype):
    y = xdrtype(5)
    assert y == 5
    assert isinstance(y, xdrlib.Integer)
    assert isinstance(y, optional_integer_type)
    assert isinstance(y, xdrlib.Optional)


@pytest.mark.parametrize('xdrtype', [
    optional_integer_type,  # direct instantiation
    # optional_integer_type(3).__class__,  # through the class of a present value
    # optional_integer_type(None).__class__, # through the class of an absent value
])
def test_absent_optional_value_instantiation(xdrtype):
    y = xdrtype(None)
    assert y == None
    assert not isinstance(y, xdrlib.Integer)
    assert isinstance(y, xdrlib.Void)
    assert isinstance(y, optional_integer_type)
    assert isinstance(y, xdrlib.Optional)


def test_optional_type_can_be_made_optional():
    new_optional_type = xdrlib.Optional(optional_integer_type)
    x = new_optional_type(3)
    y = new_optional_type(None)
    assert isinstance(x, xdrlib.Integer)
    assert isinstance(x, optional_integer_type)
    assert isinstance(x, new_optional_type)
    assert isinstance(y, xdrlib.Void)
    assert isinstance(y, optional_integer_type)
    assert isinstance(y, new_optional_type)
    px = xdrlib.TRUE.encode() + xdrlib.TRUE.encode() + xdrlib.Integer(3).encode()
    py = xdrlib.FALSE.encode()
    assert x.encode() == px
    assert y.encode() == py
    nx = new_optional_type.decode(px)
    ny = new_optional_type.decode(py)
    assert nx == x
    assert ny == y
    assert nx.encode() == px
    assert ny.encode() == py



def test_void_cannot_be_made_optional():
    with pytest.raises(TypeError):
        _ = xdrlib.Optional(xdrlib.Void)


def test_cannot_create_optional_classes_through_derived_optional_class():
    with pytest.raises(TypeError):
        optional_integer_type(xdrlib.Float)


def test_verify_class_hierarchy():
    x = optional_integer_type(3)
    y = optional_integer_type(None)
    assert optional_integer_type.__bases__ == (xdrlib.Optional,)
    assert type(x).__bases__ == (optional_integer_type, xdrlib.Integer)
    assert type(y).__bases__ == (optional_integer_type, xdrlib.Void)

