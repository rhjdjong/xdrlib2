# # Copyright (c) 2018 Ruud de Jong
# # This file is part of the xdrlib2 project which is released under the MIT license.
# # See https://github.com/rhjdjong/xdrlib2 for details.
#
import pytest
import xdrlib2 as xdrlib


optional_integer_type = xdrlib.Optional(xdrlib.Integer)


def test_optional_class_is_subclass_of_Optional():
    assert issubclass(optional_integer_type, xdrlib.Optional)


def test_optional_class_name_is_by_default_derived_from_original_class():
    assert optional_integer_type.__name__ == '*Integer'


def test_optional_integer_is_not_a_subtype_of_integer():
    assert not issubclass(optional_integer_type, xdrlib.Integer)


x = optional_integer_type(3)
xc = x.__class__

def test_present_optional_value_instantiation():
    y = optional_integer_type(5)
    assert y == 5
    assert isinstance(y, xdrlib.Integer)
    assert isinstance(y, optional_integer_type)
    assert isinstance(y, xdrlib.Optional)


def test_absent_optional_value_instantiation():
    y = optional_integer_type(None)
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
    assert isinstance(y, new_optional_type)
    px = xdrlib.TRUE._encode_() + xdrlib.TRUE._encode_() + xdrlib.Integer(3)._encode_()
    py = xdrlib.FALSE._encode_()
    assert xdrlib.encode(x) == px
    assert xdrlib.encode(y) == py
    nx = xdrlib.decode(new_optional_type, px)
    ny = xdrlib.decode(new_optional_type, py)
    assert nx == x
    assert ny == y
    assert nx._encode_() == px
    assert ny._encode_() == py



def test_void_cannot_be_made_optional():
    with pytest.raises(TypeError):
        _ = xdrlib.Optional(xdrlib.Void)


def test_cannot_create_optional_classes_through_derived_optional_class():
    with pytest.raises(TypeError):
        optional_integer_type(xdrlib.Float)


def test_verify_class_hierarchy():
    x = optional_integer_type(3)
    y = optional_integer_type(None)
    assert issubclass(optional_integer_type, xdrlib.Optional)
    assert isinstance(x, optional_integer_type)
    assert isinstance(x, xdrlib.Integer)
    assert isinstance(y, optional_integer_type)
    assert isinstance(y, xdrlib.Void)

def test_optional_fixed_length_array():
    optType = xdrlib.Optional(xdrlib.FixedArray.typedef(size=5, type=xdrlib.String.typedef(size=5)))
    strings = (
        b'a',
        b'bc',
        b'def',
        b'ghij',
        b'klmno',
    )
    yes = optType(strings)
    no = optType(None)
    assert isinstance(yes, optType)
    assert yes == list(strings)
    assert no == None
    pyes = xdrlib.encode(xdrlib.TRUE) + b'\0\0\0\x01a\0\0\0' + b'\0\0\0\x02bc\0\0' +\
           b'\0\0\0\x03def\0' + b'\0\0\0\x04ghij' + b'\0\0\0\x05klmno\0\0\0'
    pno = xdrlib.encode(xdrlib.FALSE)
    assert xdrlib.encode(yes) == pyes
    assert xdrlib.encode(no) == pno
    yes2 = xdrlib.decode(optType, pyes)
    assert yes2 == yes
    assert xdrlib.encode(yes2) == pyes
    no2 = xdrlib.decode(optType, pno)
    assert no2 == no
    assert xdrlib.encode(no2) == pno


def test_optional_variable_length_array():
    optType = xdrlib.Optional(xdrlib.VarArray.typedef(size=5, type=xdrlib.Boolean))
    booleans = (
        xdrlib.TRUE,
        xdrlib.FALSE,
        xdrlib.FALSE
    )
    yes = optType(booleans)
    no = optType(None)
    assert isinstance(yes, optType)
    assert isinstance(no, optType)
    assert isinstance(yes, xdrlib.VarArray)
    assert isinstance(no, xdrlib.Void)
    assert yes == list(booleans)
    assert no == None
    pyes = xdrlib.encode(xdrlib.TRUE) + b'\0\0\0\x03' + b'\0\0\0\x01\0\0\0\0\0\0\0\0'
    pno = xdrlib.encode(xdrlib.FALSE)
    assert xdrlib.encode(yes) == pyes
    assert xdrlib.encode(no) == pno
    yes2 = xdrlib.decode(optType, pyes)
    assert yes2 == yes
    assert xdrlib.encode(yes2) == pyes
    no2 = xdrlib.decode(optType, pno)
    assert no2 == no
    assert xdrlib.encode(no2) == pno

def test_variable_array_with_optional_elements():
    MyType = xdrlib.VarArray.typedef(size=5, type=xdrlib.Optional(xdrlib.Boolean))
    elements = (
        xdrlib.TRUE,
        xdrlib.FALSE,
        None,
        xdrlib.TRUE,
        None
    )
    my_obj = MyType(elements)
    assert isinstance(my_obj, MyType)
    assert isinstance(my_obj, xdrlib.VarArray)
    assert my_obj == list(elements)
    for e in my_obj:
        assert isinstance(e, my_obj.type)
    assert isinstance(my_obj[0], xdrlib.Boolean)
    assert isinstance(my_obj[1], xdrlib.Boolean)
    assert isinstance(my_obj[2], xdrlib.Void)
    assert isinstance(my_obj[3], xdrlib.Boolean)
    assert isinstance(my_obj[4], xdrlib.Void)
    p = b'\0\0\0\x05' + b''.join((
        b'\0\0\0\x01\0\0\0\x01',
        b'\0\0\0\x01\0\0\0\0',
        b'\0\0\0\0',
        b'\0\0\0\x01\0\0\0\x01',
        b'\0\0\0\0'
    ))
    assert xdrlib.encode(my_obj) == p
    obj2 = xdrlib.decode(MyType, p)
    assert obj2 == my_obj
    assert xdrlib.encode(obj2) == p
