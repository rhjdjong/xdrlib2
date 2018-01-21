# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest
import math
import struct
import xdrlib2 as xdrlib

binary_layout = {
    xdrlib.Float32: {'e': 8, 'f': 23, 'size': 4},
    xdrlib.Float64: {'e': 11, 'f': 52, 'size': 8},
    xdrlib.Float128: {'e': 15, 'f': 112, 'size': 16}
}

def parse_packed_data(cls, data):
    layout = binary_layout[cls]
    packed_size = layout['size']
    exponent_size = layout['e']
    fraction_size = layout['f']

    assert len(data) == packed_size

    # Convert the bytes into an integer, in order to
    # do shift and mask operations.
    number = int.from_bytes(data, 'big')
    fraction = number & ((1<<fraction_size)-1)
    number >>= fraction_size
    exponent = number & ((1<<exponent_size)-1)
    number >>= exponent_size
    signbit = number & 1
    return signbit, exponent, fraction

def build_packed_data(cls, signbit, exponent, fraction):
    layout = binary_layout[cls]
    exponent_size = layout['e']
    fraction_size = layout['f']
    packed_size = layout['size']

    number = ((signbit << (exponent_size + fraction_size)) |
              (exponent << fraction_size) | fraction )
    return number.to_bytes(packed_size, 'big')

def calculate_representation(cls, value):
    layout = binary_layout[cls]
    exponent_size = layout['e']
    fraction_size = layout['f']
    bias = (1 << (exponent_size-1)) - 1
    max_exponent = (1 << exponent_size) - 1

    signbit = 1 if math.copysign(1, value) < 0 else 0
    if math.isinf(value):
        exponent = max_exponent
        fraction = 0
    elif math.isnan(value):
        exponent = max_exponent
        packed_value = struct.pack('>d', value)
        double_fraction_size = binary_layout[xdrlib.Float64]['f']
        fraction = int.from_bytes(packed_value, 'big') & ((1 << double_fraction_size) - 1)
        if fraction_size < double_fraction_size:
            fraction >>= (double_fraction_size - fraction_size)
        elif fraction_size > double_fraction_size:
            fraction <<= (fraction_size - double_fraction_size)
    elif value == 0.0:
        exponent = 0
        fraction = 0
    else:
        m, p = math.frexp(value)
        m = abs(m)
        exponent = p - 1 + bias
        fraction = round((2*m-1) * 2**fraction_size)

    return signbit, exponent, fraction


@pytest.mark.parametrize("xdrtype", [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128]
)
def test_default_instantiation(xdrtype):
    assert xdrtype() == 0.0

@pytest.mark.parametrize("xdrtype", [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128]
)
@pytest.mark.parametrize("value", [
    0.0, -0.5, 0.375, -0.1
])
def test_encoding_and_decoding_of_regular_values(xdrtype, value):
    if xdrtype == xdrlib.Float32:
        value = struct.unpack('>f', struct.pack('>f', value))[0]
    s, e, f = calculate_representation(xdrtype, value)
    packed_data = build_packed_data(xdrtype, s, e, f)

    # Encoding-decoding roundtrip
    x = xdrtype(value)
    p = x.encode()
    assert p == packed_data
    y = xdrtype.decode(p)
    assert isinstance(y, xdrtype)
    assert x == y

    # Decoding-encoding roundtrip
    x = xdrtype.decode(packed_data)
    assert isinstance(x, xdrtype)
    assert x == value
    p = x.encode()
    assert p == packed_data


def test_encoding_and_decoding_underflow_values():
    # to be provided