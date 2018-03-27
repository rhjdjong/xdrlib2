# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import xdrlib2 as xdrlib
import pytest


class MyFixedArray(xdrlib.FixedArray, size=10, type=xdrlib.Integer):
    pass


class MyVarArray(xdrlib.VarArray):
    size = 10
    type = xdrlib.UnsignedHyper


class MyEnumVarArray(xdrlib.VarArray):
    size = 10
    type = xdrlib.Enumeration.typedef('Color', RED=2, YELLOW=3, BLUE=5)


def test_fixed_length_array_through_argument():
    int_seq = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4]
    x = MyFixedArray(int_seq)
    assert isinstance(x, MyFixedArray)
    assert all(isinstance(i, MyFixedArray.type) for i in x)
    assert x == int_seq
    p = x.encode()
    assert p == b''.join(xdrlib.Integer(x).encode() for x in int_seq)
    n = MyFixedArray.decode(p)
    assert isinstance(n, MyFixedArray)
    assert n == x
    assert n.encode() == p


def test_default_instantiation_fixed_opaque_has_all_zero_bytes():
    x = MyFixedArray()
    assert isinstance(x, MyFixedArray)
    assert x == [0] * 10
    assert all(isinstance(i, MyFixedArray.type) for i in x)


def test_var_length_array_through_argument():
    int_seq = [0, 1, 2, 3, 4]
    x = MyVarArray(int_seq)
    assert isinstance(x, MyVarArray)
    assert all(isinstance(i, MyVarArray.type) for i in x)
    assert x == int_seq
    p = x.encode()
    assert p == xdrlib.UnsignedInteger(len(int_seq)).encode() +\
           b''.join(xdrlib.UnsignedHyper(x).encode() for x in int_seq)
    n = MyVarArray.decode(p)
    assert isinstance(n, MyVarArray)
    assert n == x
    assert n.encode() == p


def test_default_instantiation_variable_is_empty_bytes():
    x = MyVarArray()
    assert x == []
    assert x.encode() == b'\0\0\0\0'


def test_fixed_length_instantiation_fails_with_wrong_sized_argument():
    with pytest.raises(ValueError):
        MyFixedArray([0, 1, 2])
    with pytest.raises(ValueError):
        MyFixedArray(range(12))


@pytest.mark.parametrize('xdrtype', [
    MyFixedArray,
    MyVarArray,
    MyEnumVarArray
])
def test_subclassing_with_size_fails(xdrtype):
    with pytest.raises(TypeError):
        class InvalidSubClass(xdrtype, size=5):
            pass


@pytest.mark.parametrize('xdrtype', [
    MyFixedArray,
    MyVarArray,
    MyEnumVarArray
])
def test_subclassing_with_type_fails(xdrtype):
    with pytest.raises(TypeError):
        class InvalidSubClass(xdrtype, type=xdrlib.Float):
            pass


@pytest.mark.parametrize('xdrtype', [
    MyFixedArray,
    MyVarArray,
    MyEnumVarArray
])
def test_subclassing_without_changes_works(xdrtype):
    class Other(xdrtype):
        pass
    assert Other.size == xdrtype.size
    assert Other.type == xdrtype.type


@pytest.mark.parametrize('xdrtype', [
    MyFixedArray,
    MyVarArray,
    MyEnumVarArray
])
def test_modifying_size_fails(xdrtype):
    with pytest.raises(AttributeError):
        xdrtype._size = 5


@pytest.mark.parametrize('xdrtype', [
    MyFixedArray,
    MyVarArray,
    MyEnumVarArray
])
def test_modifying_size_fails(xdrtype):
    with pytest.raises(AttributeError):
        xdrtype.type = 5


def test_substring_replacement_works_for_fixed_size_array():
    b = MyFixedArray(range(-5, 5))
    b[3:5] = [100, 200]
    assert b == [-5, -4, -3, 100, 200, 0, 1, 2, 3, 4]
    assert b.encode() == b''.join((b.type(x)).encode() for x in [-5, -4, -3, 100, 200, 0, 1, 2, 3, 4])


def test_modifying_length_fails_for_fixed_size_array():
    b = MyFixedArray(range(-5, 5))
    with pytest.raises(ValueError):
        b[3:8] = [0, 1]
    with pytest.raises(ValueError):
        del b[3:8]
    with pytest.raises(ValueError):
        b += [5, 6]
    with pytest.raises(ValueError):
        b *= 2
    with pytest.raises(ValueError):
        b.append(7)
    with pytest.raises(ValueError):
        b.extend([8, 9])
    with pytest.raises(ValueError):
        b.remove(3)
    with pytest.raises(ValueError):
        b.pop(5)
    with pytest.raises(ValueError):
        b.clear()


def test_substring_modification_works_for_variable_length():
    b = MyVarArray(range(5))
    b[3:5] = [20, 21, 22, 23]
    assert b == [0, 1, 2, 20, 21, 22, 23]
    b[-1] = 10
    assert b == [0, 1, 2, 20, 21, 22, 10]
    assert b.encode() == b'\0\0\0\x07' + b''.join(xdrlib.UnsignedHyper(x).encode() for x in [0, 1, 2, 20, 21, 22, 10])
    del b[1:5]
    assert b == [0, 22, 10]
    assert b.encode() == b'\0\0\0\x03' + b''.join(xdrlib.UnsignedHyper(x).encode() for x in [0, 22, 10])
    b += [5, 6]
    assert b == [0, 22, 10, 5, 6]
    b *= 2
    assert b == [0, 22, 10, 5, 6, 0, 22, 10, 5, 6]
    b.clear()
    assert b == []
    b.append(48)
    assert b == [48]
    b.extend([1, 2, 3, 4, 5])
    assert b == [48, 1, 2, 3, 4, 5]
    b.remove(1)
    assert b == [48, 2, 3, 4, 5]
    assert b.pop(3) == 4
    assert b == [48, 2, 3, 5]


def test_substring_modification_fails_if_size_exceeds_maximum_length():
    b = MyVarArray(range(5))
    with pytest.raises(ValueError):
        b[3:5] = range(10)
    with pytest.raises(ValueError):
        b += list(range(6))
    with pytest.raises(ValueError):
        b *= 3
    b *= 2
    assert b == [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
    with pytest.raises(ValueError):
        b.append(5)
    del b[5:]
    assert b == [0, 1, 2, 3, 4]
    with pytest.raises(ValueError):
        b.extend(range(6))


@pytest.mark.parametrize('seqtype', [
    MyFixedArray,
    MyVarArray,
    MyEnumVarArray
])
@pytest.mark.parametrize('invalid', [
    None,
    {},
    [1,2,3],
    'string',
    (b'', b''),
])
def test_item_replacement_fails_with_wrong_data_type(seqtype, invalid):
    b = seqtype([2, 3, 5, 2, 3, 5, 2, 3, 5, 2])
    if invalid is not None and seqtype is not MyEnumVarArray:
        with pytest.raises((ValueError, TypeError)):
            b[3] = invalid


@pytest.mark.parametrize('seqtype', [
    MyFixedArray,
    MyVarArray,
    MyEnumVarArray
])
@pytest.mark.parametrize('invalid', [
    None,
    {int: 5, float: 6},
    [1,2,3],
    'string',
])
def test_slice_replacement_fails_with_wrong_data_type(seqtype, invalid):
    b = seqtype([2, 3, 5, 2, 3, 5, 2, 3, 5, 2])
    with pytest.raises((ValueError, TypeError)):
        b[3:5] = invalid

def test_optional_fixed_length_array():
    optType = xdrlib.Optional(xdrlib.FixedArray.typedef(size=5, type=xdrlib.String(size=5)))
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
    pyes = xdrlib.TRUE.encode() +b'\0\0\0\x01a\0\0\0' + b'\0\0\0\x02bc\0\0' +\
           b'\0\0\0\x03def\0' + b'\0\0\0\x04ghij' + b'\0\0\0\x05klmno\0\0\0'
    pno = xdrlib.FALSE.encode()
    assert yes.encode() == pyes
    assert no.encode() == pno
    yes2 = optType.decode(pyes)
    assert yes2 == yes
    assert yes2.encode() == pyes
    no2 = optType.decode(pno)
    # assert no2 == no
    assert no2.encode() == pno


def test_optional_variable_length_array():
    optType = xdrlib.Optional(xdrlib.VarArray(size=5, type=xdrlib.Boolean))
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
    pyes = xdrlib.TRUE.encode() + b'\0\0\0\x03' + b'\0\0\0\x01\0\0\0\0\0\0\0\0'
    pno = xdrlib.FALSE.encode()
    assert yes.encode() == pyes
    assert no.encode() == pno
    yes2 = optType.decode(pyes)
    assert yes2 == yes
    assert yes2.encode() == pyes
    no2 = optType.decode(pno)
    assert no2 == no
    assert no2.encode() == pno

def test_variable_array_with_optional_elements():
    MyType = xdrlib.VarArray(size=5, type=xdrlib.Optional(xdrlib.Boolean))
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
    assert issubclass(my_obj.type, xdrlib.Optional)
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
    assert my_obj.encode() == p
    obj2 = MyType.decode(p)
    assert obj2 == my_obj
    assert obj2.encode() == p
