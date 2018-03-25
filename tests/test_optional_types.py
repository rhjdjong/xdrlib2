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


def test_optional_decorator_is_idempotent():
    new_optional_type = xdrlib.Optional(optional_integer_type)
    assert new_optional_type is optional_integer_type


def test_void_cannot_be_made_optional():
    with pytest.raises(TypeError):
        _ = xdrlib.Optional(xdrlib.Void)


def test_cannot_create_optional_classes_through_derived_optional_class():
    with pytest.raises(TypeError):
        optional_integer_type(xdrlib.Float)


def test_verify_class_hierarchy():
    x = optional_integer_type(3)
    y = optional_integer_type()
    assert optional_integer_type.__bases__ == (xdrlib.Optional,)
    assert type(x).__bases__ == (optional_integer_type, xdrlib.Integer)
    assert type(y).__bases__ == (optional_integer_type, xdrlib.Void)

