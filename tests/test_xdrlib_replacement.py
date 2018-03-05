# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

# This file contains a copy of the tests present in lib/test/test_xdrlib.py.
# modified to use xdrlib2 and pytest

import pytest
import xdrlib2 as xdrlib


def test_xdr():
    p = xdrlib.Packer()

    s = b'hello world'
    a = [b'what', b'is', b'hapnin', b'doctor']

    p.pack_int(42)
    p.pack_int(-17)
    p.pack_uint(9)
    p.pack_bool(True)
    p.pack_bool(False)
    p.pack_uhyper(45)
    p.pack_float(1.9)
    p.pack_double(1.9)
    p.pack_string(s)
    p.pack_list(range(5), p.pack_uint)
    p.pack_array(a, p.pack_string)

    # now verify
    data = p.get_buffer()
    up = xdrlib.Unpacker(data)

    # self.assertEqual(up.get_position(), 0)
    assert up.get_position() == 0

    # self.assertEqual(up.unpack_int(), 42)
    # self.assertEqual(up.unpack_int(), -17)
    # self.assertEqual(up.unpack_uint(), 9)
    # self.assertTrue(up.unpack_bool() is True)
    assert up.unpack_int() == 42
    assert up.unpack_int() == -17
    assert up.unpack_uint() == 9
    assert up.unpack_bool() is True

    # remember position
    pos = up.get_position()
    # self.assertTrue(up.unpack_bool() is False)
    assert up.unpack_bool() is False

    # rewind and unpack again
    up.set_position(pos)
    # self.assertTrue(up.unpack_bool() is False)
    assert up.unpack_bool() is False

    # self.assertEqual(up.unpack_uhyper(), 45)
    # self.assertAlmostEqual(up.unpack_float(), 1.9)
    # self.assertAlmostEqual(up.unpack_double(), 1.9)
    # self.assertEqual(up.unpack_string(), s)
    # self.assertEqual(up.unpack_list(up.unpack_uint), list(range(5)))
    # self.assertEqual(up.unpack_array(up.unpack_string), a)
    assert up.unpack_uhyper() == 45
    assert up.unpack_float() == pytest.approx(1.9)
    assert up.unpack_double() == pytest.approx(1.9)
    assert up.unpack_string() == s
    assert up.unpack_list(up.unpack_uint) == list(range(5))
    assert up.unpack_array(up.unpack_string) == a

    up.done()
    # self.assertRaises(EOFError, up.unpack_uint)
    with pytest.raises(EOFError):
        up.unpack_uint()


class TestConversionErrorTest:
    # def setUp(self):
    #     self.packer = xdrlib.Packer()
    #
    @pytest.fixture(autouse=True)
    def setup(self):
        self.packer = xdrlib.Packer()
        yield
        self.packer.reset()

    # def test_assertRaisesConversion(self, *args):
    #     self.assertRaises(xdrlib.ConversionError, *args)

    def test_pack_int(self):
        # self.assertRaisesConversion(self.packer.pack_int, 'string')
        with pytest.raises(xdrlib.ConversionError):
            self.packer.pack_int('string')

    def test_pack_uint(self):
        # self.assertRaisesConversion(self.packer.pack_uint, 'string')
        with pytest.raises(xdrlib.ConversionError):
            self.packer.pack_uint('string')

    def test_float(self):
        # self.assertRaisesConversion(self.packer.pack_float, 'string')
        with pytest.raises(xdrlib.ConversionError):
            self.packer.pack_float('string')

    def test_double(self):
        # self.assertRaisesConversion(self.packer.pack_double, 'string')
        with pytest.raises(xdrlib.ConversionError):
            self.packer.pack_double('string')

    def test_uhyper(self):
        # self.assertRaisesConversion(self.packer.pack_uhyper, 'string')
        with pytest.raises(xdrlib.ConversionError):
            self.packer.pack_uhyper('string')
