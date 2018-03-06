# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import math
import struct
from decimal import localcontext, ROUND_HALF_EVEN

import pytest

import xdrlib2 as xdrlib

precision = {
    xdrlib.Float32: 1e-6,
    xdrlib.Float64: 1e-15,
    xdrlib.Float128: 1e-15
}


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
def test_default_instantiation(xdrtype):
    n = xdrtype()
    assert isinstance(n, xdrtype)
    assert n == 0.0
    assert n == 0
    packed = n.encode()
    assert len(packed) == (1 + xdrtype._exponent_size + xdrtype._fraction_size) / 8
    assert all(b == 0 for b in packed)
    unpacked = xdrtype.decode(packed)
    assert unpacked == n
    assert isinstance(unpacked, xdrtype)
    assert unpacked.encode() == packed


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('param,value', [
    (-3.14, -3.14),
    (314, 314.0),
])
def test_instantiation_from_number(xdrtype, param, value):
    n = xdrtype(param)
    assert isinstance(n, xdrtype)
    assert n == pytest.approx(value, precision[xdrtype])
    packed = n.encode()
    m = xdrtype.decode(packed)
    assert isinstance(m, xdrtype)
    assert m.encode() == packed


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('param,value', [
    ('  -3.14  ', '-3.14'),
    ('  \u0663.\u0661\u0664  ', '3.14'),
    ('\N{EM SPACE}3.14\N{EN SPACE}', '3.14')
])
def test_instantiation_from_string(xdrtype, param, value):
    n = xdrtype(param)
    assert isinstance(n, xdrtype)
    value = float(value)
    assert n == pytest.approx(value, precision[xdrtype])
    packed = n.encode()
    m = xdrtype.decode(packed)
    assert isinstance(m, xdrtype)
    assert m.encode() == packed


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('param,value', [
    (b'  -3.14  ', '-3.14'),
    (b'  3.14  ', '3.14'),
])
def test_instantiation_from_bytes(xdrtype, param, value):
    n = xdrtype(param)
    assert isinstance(n, xdrtype)
    value = float(value)
    assert n == pytest.approx(value, precision[xdrtype])
    packed = n.encode()
    m = xdrtype.decode(packed)
    assert isinstance(m, xdrtype)
    assert m.encode() == packed


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('invalid', [
    "  0x3.1  ",
    "  -0x3.p-1  ",
    "++3.14",
    "-+3.14",
    ".nan",
    "+.inf",
    ".",
    "-.",
    "-1.7d29",
    "3D-14",
])
def test_invalid_instantiation_string_raises_ValueError(xdrtype, invalid):
    with pytest.raises(ValueError):
        xdrtype(invalid)


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('invalid', [
    {},
    (),
    [],
    object(),
])
def test_invalid_instantiation_parameter_type_raises_TypeError(xdrtype, invalid):
    with pytest.raises(TypeError) as exc_info:
        xdrtype(invalid)
    assert f"not '{invalid.__class__.__name__:s}'" in str(exc_info.value)


@pytest.mark.parametrize('value', [
    float('-inf'),
    ((1 << 24) - 1) * 2 ** (127 - 23),
    2 ** -126,
    2 ** -127,
    2 ** -149,
    1.0,
    -2.0,
    0.0,
    -0.0,
    math.pi,
    1 / 3,
])
def test_encoding_for_Float32(value):
    n = xdrlib.Float32(value)
    assert n == pytest.approx(value, precision[xdrlib.Float32])
    packed = struct.pack('>f', value)
    assert n.encode() == packed
    n2 = xdrlib.Float32.decode(packed)
    assert n2.signbit == n.signbit
    assert n2.exponent == n.exponent
    assert n2.fraction == n.fraction


@pytest.mark.parametrize('value', [
    float('-inf'),
    2 ** 1024 - 2 ** (1023-52),
    2 ** -1022,
    2 ** -1022 - 2 ** -1074,
    2 ** -1074,
    2 ** -1075,
    1.0,
    -2.0,
    0.0,
    -0.0,
    math.pi,
    1 / 3,
])
def test_encoding_for_Float64(value):
    n = xdrlib.Float64(value)
    assert n == pytest.approx(value, precision[xdrlib.Float64])
    packed = struct.pack('>d', value)
    assert n.encode() == packed
    n2 = xdrlib.Float64.decode(packed)
    assert n2.signbit == n.signbit
    assert n2.exponent == n.exponent
    assert n2.fraction == n.fraction


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
def test_maximum_value(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype._fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        max_normal_value = ctx.subtract(ctx.power(2, xdrtype._exponent_bias + 1),
                                        ctx.power(2, xdrtype._exponent_bias - xdrtype._fraction_size))
        n = xdrtype(str(max_normal_value))
        assert n.exponent == xdrtype._max_exponent - 1
        assert n.fraction == xdrtype._fraction_mask
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
def test_subnormal(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype._fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        for i in range(xdrtype._fraction_size):
            value = ctx.power(2, - xdrtype._exponent_bias - i)
            n = xdrtype(str(value))
            fraction = 1 << (xdrtype._fraction_size - i - 1)
            packed = fraction.to_bytes(xdrtype._packed_size, 'big')
            assert n.encode() == packed
            unpacked = xdrtype.decode(packed)
            assert n == unpacked
            assert unpacked.encode() == packed


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
def test_smallest_normal_number(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype._fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        smallest_normal = ctx.power(2, 1 - xdrtype._exponent_bias)
        n = xdrtype(str(smallest_normal))
        assert n.exponent == 1
        assert n.fraction == 0
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
def test_largest_subnormal_number(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype._fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        power_of_two = ctx.power(2, 1 - xdrtype._exponent_bias - xdrtype._fraction_size)
        largest_subnormal = ctx.multiply(xdrtype._fraction_mask, power_of_two)
        n = xdrtype(str(largest_subnormal))
        assert n.exponent == 0
        assert n.fraction == xdrtype._fraction_mask
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
def test_smallest_subnormal_numbers(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype._fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        exponent = 1 - xdrtype._exponent_bias - xdrtype._fraction_size
        value = ctx.power(2, exponent)
        n = xdrtype(str(value))
        assert n.exponent == 0
        assert n.fraction == 1
        assert xdrtype.decode(n.encode()) == n

@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
def test_correct_rounding_of_half_smallest_subnormal_number(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype._fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        exponent = 1 - xdrtype._exponent_bias - xdrtype._fraction_size
        smallest_subnormal = ctx.power(2, exponent)
        n = xdrtype(str(smallest_subnormal))
        assert n.exponent == 0
        assert n.fraction == 1
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('value,ratio', [
    (0, (0, 1)),
    (1, (1, 1)),
    (0.5, (1, 2)),
    (0.375, (3, 8))
])
def test_as_integer_ratio(xdrtype, value, ratio):
    n = xdrtype(value)
    assert n.as_integer_ratio() == ratio


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('value,exception', [
    (float('inf'), OverflowError),
    (float('nan'), ValueError)
])
def test_as_integer_ratio_raises_exception_for_inf_and_nan_value(xdrtype, value, exception):
    n = xdrtype(value)
    with pytest.raises(exception):
        n.as_integer_ratio()


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('value,result', [
    (3.0, True),
    (1.5, False)
])
def test_is_integer(xdrtype, value, result):
    n = xdrtype(value)
    assert n.is_integer() == result


def test_is_integer_quadruple_values():
    n = xdrlib.Float128('1.3545e1000')
    assert n.is_integer()


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('hexstr,value', [
    ('0', 0.0),
    ('-0x0.0', -0.0),
    ('0x1.0000000p10', 2**10),
    ('0x1.5555555555555555555555555555555555555p-2', 1/3),
    ('-inf', '-inf'),
    ('nan', 'nan')
])
def test_fromhex(xdrtype, hexstr, value):
    if 'nan' in hexstr:
        assert math.isnan(xdrtype.fromhex(hexstr))
    elif 'inf' in hexstr:
        assert math.isinf(xdrtype.fromhex(hexstr))
    else:
        assert xdrtype.fromhex(hexstr) == xdrtype(value)

