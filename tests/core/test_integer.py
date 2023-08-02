# Copyright (c) 2023 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest

from xdrlib2.core.integer import Integer


@pytest.mark.parametrize(
    "value, encoded",
    [
        (0, b"\x00\x00\x00\x00"),
        (324, b"\x00\x00\x01D"),
        (2**31 - 1, b"\x7f\xff\xff\xff"),
        (-527, b"\xff\xff\xfd\xf1"),
        (-(2**31), b"\x80\x00\x00\x00"),
    ],
)
def test_integer_encoding_and_decoding(value: int, encoded: bytes) -> None:
    x = Integer(value)
    assert bytes(x) == encoded
    y = Integer._decode(encoded)
    assert isinstance(y, Integer)
    assert y == x
    assert y == value
    assert bytes(y) == encoded
