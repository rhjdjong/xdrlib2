# Copyright (c) 2023 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest

from xdrlib2.core.integer import Hyper, Integer, UnsignedHyper, UnsignedInteger, XdrInteger


class TestInteger:
    xdr_type = Integer
    value_encoding = {
        0: b"\x00\x00\x00\x00",
        324: b"\x00\x00\x01D",
        2**31 - 1: b"\x7f\xff\xff\xff",
        -527: b"\xff\xff\xfd\xf1",
        -(2**31): b"\x80\x00\x00\x00",
    }

    @pytest.mark.parametrize("value", [t for t in value_encoding])
    def test_instantiation(self, value: int) -> None:
        x = self.xdr_type(value)
        assert isinstance(x, self.xdr_type)
        assert x == value

    @pytest.mark.parametrize("value, encoded", [(v, e) for v, e in value_encoding.items()])
    def test_encoding_and_decoding(self, value: int, encoded: bytes) -> None:
        x = self.xdr_type(value)
        y = self.xdr_type.from_bytes(encoded)
        assert type(y) is self.xdr_type
        assert x == y
        assert x.to_bytes() == encoded

    @pytest.mark.parametrize("value", [min(v for v in value_encoding) - 1, max(v for v in value_encoding) + 1])
    def test_invalid_value(self, value: int) -> None:
        with pytest.raises(ValueError):
            self.xdr_type(value)


class TestUnsignedInteger:
    xdr_type = UnsignedInteger
    value_encoding = {
        0: b"\x00\x00\x00\x00",
        324: b"\x00\x00\x01D",
        2**31 - 1: b"\x7f\xff\xff\xff",
        2**31: b"\x80\x00\x00\x00",
        0xDEADBEEF: b"\xde\xad\xbe\xef",
        2**32 - 1: b"\xff\xff\xff\xff",
    }

    @pytest.mark.parametrize("value", [t for t in value_encoding])
    def test_instantiation(self, value: int) -> None:
        x = self.xdr_type(value)
        assert isinstance(x, self.xdr_type)
        assert x == value

    @pytest.mark.parametrize("value, encoded", [(v, e) for v, e in value_encoding.items()])
    def test_encoding_and_decoding(self, value: int, encoded: bytes) -> None:
        x = self.xdr_type(value)
        y = self.xdr_type.from_bytes(encoded)
        assert type(y) is self.xdr_type
        assert x == y
        assert x.to_bytes() == encoded

    @pytest.mark.parametrize("value", [min(v for v in value_encoding) - 1, max(v for v in value_encoding) + 1])
    def test_invalid_value(self, value: int) -> None:
        with pytest.raises(ValueError):
            self.xdr_type(value)


class TestHyper:
    xdr_type = Hyper
    value_encoding = {
        0: b"\x00\x00\x00\x00\x00\x00\x00\x00",
        324: b"\x00\x00\x00\x00\x00\x00\x01D",
        2**31 - 1: b"\x00\x00\x00\x00\x7f\xff\xff\xff",
        2**63 - 1: b"\x7f\xff\xff\xff\xff\xff\xff\xff",
        -527: b"\xff\xff\xff\xff\xff\xff\xfd\xf1",
        -(2**31): b"\xff\xff\xff\xff\x80\x00\x00\x00",
        -(2**63): b"\x80\x00\x00\x00\x00\x00\x00\x00",
    }

    @pytest.mark.parametrize("value", [t for t in value_encoding])
    def test_instantiation(self, value: int) -> None:
        x = self.xdr_type(value)
        assert isinstance(x, self.xdr_type)
        assert x == value

    @pytest.mark.parametrize("value, encoded", [(v, e) for v, e in value_encoding.items()])
    def test_encoding_and_decoding(self, value: int, encoded: bytes) -> None:
        x = self.xdr_type(value)
        y = self.xdr_type.from_bytes(encoded)
        assert type(y) is self.xdr_type
        assert x == y
        assert x.to_bytes() == encoded

    @pytest.mark.parametrize("value", [min(v for v in value_encoding) - 1, max(v for v in value_encoding) + 1])
    def test_invalid_value(self, value: int) -> None:
        with pytest.raises(ValueError):
            self.xdr_type(value)


class TestUnsignedHyper:
    xdr_type = UnsignedHyper
    value_encoding = {
        0: b"\x00\x00\x00\x00\x00\x00\x00\x00",
        324: b"\x00\x00\x00\x00\x00\x00\x01D",
        2**31 - 1: b"\x00\x00\x00\x00\x7f\xff\xff\xff",
        2**31: b"\x00\x00\x00\x00\x80\x00\x00\x00",
        0xDEADBEEF: b"\x00\x00\x00\x00\xde\xad\xbe\xef",
        2**32 - 1: b"\x00\x00\x00\x00\xff\xff\xff\xff",
        0xC0FFEECAFEFACADE: b"\xc0\xff\xee\xca\xfe\xfa\xca\xde",
        2**64 - 1: b"\xff\xff\xff\xff\xff\xff\xff\xff",
    }

    @pytest.mark.parametrize("value", [t for t in value_encoding])
    def test_instantiation(self, value: int) -> None:
        x = self.xdr_type(value)
        assert isinstance(x, self.xdr_type)
        assert x == value

    @pytest.mark.parametrize("value, encoded", [(v, e) for v, e in value_encoding.items()])
    def test_encoding_and_decoding(self, value: int, encoded: bytes) -> None:
        x = self.xdr_type(value)
        y = self.xdr_type.from_bytes(encoded)
        assert type(y) is self.xdr_type
        assert x == y
        assert x.to_bytes() == encoded

    @pytest.mark.parametrize("value", [min(v for v in value_encoding) - 1, max(v for v in value_encoding) + 1])
    def test_invalid_value(self, value: int) -> None:
        with pytest.raises(ValueError):
            self.xdr_type(value)


class TestXdrInteger:
    xdr_type = XdrInteger

    def test_abstract_type_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            self.xdr_type(0)

    def test_alias_for_abstract_type_not_allowed(self) -> None:
        with pytest.raises(TypeError):
            self.xdr_type.typedef("AnAlias")

    def test_incomplete_typedef_not_allowed(self) -> None:
        with pytest.raises(TypeError):
            self.xdr_type.typedef("dummy", bits=16)
        with pytest.raises(TypeError):
            self.xdr_type.typedef("dummy", signed=False)

    def test_custom_concrete_type(self) -> None:
        short = self.xdr_type.typedef("short", bits=16, signed=False)
        x = short(512)
        e = x.to_bytes()
        assert e == b"\x02\x00\x00\x00"
        y = short.from_bytes(e)
        assert type(y) is short
        assert y == x

    def test_invalid_typedef(self) -> None:
        with pytest.raises(TypeError):
            Integer.typedef("Subtype", signed=False)
