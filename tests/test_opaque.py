# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import xdrlib2 as xdrlib
import pytest


class MyFixedOpaque(xdrlib.FixedOpaque, size=10):
    pass


class MyVarOpaque(xdrlib.VarOpaque):
    size = 10

class MyString(xdrlib.String):
    size = 10


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


@pytest.mark.parametrize('xdrtype', [
    MyVarOpaque,
    MyString
])
def test_var_length_opaque_through_argument(xdrtype):
    byte_seq = b'0123456789'
    x = xdrtype(byte_seq)
    assert isinstance(x, xdrtype)
    assert x == byte_seq
    p = x.encode()
    assert p == b'\0\0\0\x0a' + byte_seq + b'\0\0'
    n = xdrtype.decode(p)
    assert isinstance(n, xdrtype)
    assert n == x
    assert n.encode() == p


def test_default_instantiation_fixed_opaque_has_all_zero_bytes():
    x = MyFixedOpaque()
    assert isinstance(x, MyFixedOpaque)
    assert x == b'\0' * 10


@pytest.mark.parametrize('xdrtype', [
    MyVarOpaque,
    MyString
])
def test_default_instantiation_variable_is_empty_bytes(xdrtype):
    x = xdrtype()
    assert x == b''
    assert x.encode() == b'\0\0\0\0'


def test_fixed_length_instantiation_fails_with_wrong_sized_argument():
    with pytest.raises(ValueError):
        MyFixedOpaque(b'too short')
    with pytest.raises(ValueError):
        MyFixedOpaque(b'way too long')


def test_subclassing_with_size_failse():
    with pytest.raises(TypeError):
        class InvalidSubClass(MyFixedOpaque, size=5):
            pass


def test_subclassing_without_changes_works():
    class Other(MyFixedOpaque):
        pass
    assert Other.size == MyFixedOpaque.size


def test_modifying_size_fails():
    with pytest.raises(AttributeError):
        MyFixedOpaque._size = 5


def test_substring_replacement_works_for_fixed_size_opaque():
    b = MyFixedOpaque(b'abcdefghij')
    b[3:5] = b'xy'
    assert b == b'abcxyfghij'
    assert b.encode() == b'abcxyfghij' + b'\0\0'


def test_modifying_length_fails_for_fixed_size_opaque():
    b = MyFixedOpaque(b'abcdefghij')
    with pytest.raises(ValueError):
        b[3:8] = b'xy'
    with pytest.raises(ValueError):
        del b[3:8]
    with pytest.raises(ValueError):
        b += b'klm'
    with pytest.raises(ValueError):
        b *= 2
    with pytest.raises(ValueError):
        b.append(0x30)
    with pytest.raises(ValueError):
        b.extend(b'klm')
    with pytest.raises(ValueError):
        b.remove(ord('a'))
    with pytest.raises(ValueError):
        b.pop(3)
    with pytest.raises(ValueError):
        b.clear()


@pytest.mark.parametrize('xdrtype', [
    MyVarOpaque,
    MyString
])
def test_substring_modification_works_for_variable_length(xdrtype):
    b = xdrtype(b'abcde')
    b[3:5] = b'xyz12'
    assert b == b'abcxyz12'
    b[-1] = 0x33
    assert b == b'abcxyz13'
    assert b.encode() == b'\0\0\0\x08' b'abcxyz13'
    del b[1:6]
    assert b == b'a13'
    assert b.encode() == b'\0\0\0\x03' b'a13' b'\0'
    b += b'56'
    assert b == b'a1356'
    b *= 2
    assert b == b'a1356a1356'
    b.clear()
    assert b == b''
    b.append(0x30)
    assert b == b'0'
    b.extend(b'12345')
    assert b == b'012345'
    b.remove(0x31)
    assert b == b'02345'
    assert b.pop(3) == 0x34
    assert b == b'0235'


@pytest.mark.parametrize('xdrtype', [
    MyVarOpaque,
    MyString
])
def test_substring_modification_fails_if_size_exceeds_maximum_length(xdrtype):
    b = xdrtype(b'abcde')
    with pytest.raises(ValueError):
        b[3:5] = b'xyz123456'
    with pytest.raises(ValueError):
        b += b'klmnopqrst'
    with pytest.raises(ValueError):
        b *= 3
    b *= 2
    assert b == b'abcdeabcde'
    with pytest.raises(ValueError):
        b.append(0x30)
    del b[5:]
    assert b == b'abcde'
    with pytest.raises(ValueError):
        b.extend(b'klmnopq')


@pytest.mark.parametrize('seqtype', [
    MyFixedOpaque,
    MyVarOpaque,
    MyString
])
@pytest.mark.parametrize('invalid', [
    None,
    3.14,
    {},
    [1,2,3],
    'string',
    (b'', b''),
])
def test_item_replacement_fails_with_wrong_data_type(seqtype, invalid):
    b = seqtype(b'0123456789')
    with pytest.raises(ValueError):
        b[3] = invalid


@pytest.mark.parametrize('seqtype', [
    MyFixedOpaque,
    MyVarOpaque,
    MyString
])
@pytest.mark.parametrize('invalid', [
    None,
    3.14,
    {int: 5, float: 6},
    [1,2,3],
    'string',
])
def test_slice_replacement_fails_with_wrong_data_type(seqtype, invalid):
    b = seqtype(b'0123456789')
    with pytest.raises((ValueError, TypeError)):
        b[3:5] = invalid


def test_optional_fixed_length_opaque():
    optType = xdrlib.Optional(xdrlib.FixedOpaque.typedef(size=5))
    byte_str = b'\0\xff\xab\xcd\x01'
    yes = optType(byte_str)
    no = optType(None)
    assert isinstance(yes, optType)
    assert yes == byte_str
    assert no == None
    pyes = xdrlib.TRUE.encode() + byte_str + b'\0\0\0'
    pno = xdrlib.FALSE.encode()
    assert yes.encode() == pyes
    assert no.encode() == pno
    yes2 = optType.decode(pyes)
    assert yes2 == yes
    assert yes2.encode() == pyes
    no2 = optType.decode(pno)
    assert no2 == no
    assert no2.encode() == pno


@pytest.mark.parametrize('seqtype', [
    MyVarOpaque,
    MyString
])
def test_optional_variable_length_opaque(seqtype):
    optType = xdrlib.Optional(seqtype)
    byte_str = b'\xff\xab\xcd\x01'
    yes = optType(byte_str)
    no = optType(None)
    assert isinstance(yes, optType)
    assert isinstance(no, optType)
    assert isinstance(yes, seqtype)
    assert isinstance(no, xdrlib.Void)
    assert yes == byte_str
    assert no == None
    pyes = xdrlib.TRUE.encode() + b'\0\0\0\x04' + byte_str
    pno = xdrlib.FALSE.encode()
    assert yes.encode() == pyes
    assert no.encode() == pno
    yes2 = optType.decode(pyes)
    assert yes2 == yes
    assert yes2.encode() == pyes
    no2 = optType.decode(pno)
    assert no2 == no
    assert no2.encode() == pno
