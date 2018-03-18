# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import math
import struct
from decimal import localcontext, ROUND_HALF_EVEN

import pytest

import xdrlib2 as xdrlib

precision = {
    xdrlib.Float: 1e-6,
    xdrlib.Double: 1e-15,
    xdrlib.Quadruple: 1e-15
}


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_default_instantiation(xdrtype):
    n = xdrtype()
    assert isinstance(n, xdrtype)
    assert n == 0.0
    assert n == 0
    packed = n.encode()
    assert len(packed) == (1 + xdrtype.exponent_size + xdrtype.fraction_size) / 8
    assert all(b == 0 for b in packed)
    unpacked = xdrtype.decode(packed)
    assert unpacked == n
    assert isinstance(unpacked, xdrtype)
    assert unpacked.encode() == packed


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
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
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
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
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
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
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
@pytest.mark.parametrize('value', [
    (xdrlib.Float('3.14')),
    (xdrlib.Double('3.14')),
    (xdrlib.Quadruple('3.14'))
])
def test_instantiation_from_XDR_type(xdrtype, value):
    n = xdrtype(value)
    assert isinstance(n, xdrtype)
    if value.fraction_size > xdrtype.fraction_size:
        assert n == pytest.approx(value, precision[xdrtype])
    else:
        assert n == value


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
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
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
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
def test_encoding_for_Float(value):
    n = xdrlib.Float(value)
    assert n == pytest.approx(value, precision[xdrlib.Float])
    packed = struct.pack('>f', value)
    assert n.encode() == packed
    n2 = xdrlib.Float.decode(packed)
    assert n2.signbit == n.signbit
    assert n2.exponent == n.exponent
    assert n2.fraction == n.fraction


@pytest.mark.parametrize('value', [
    float('-inf'),
    2 ** 1024 - 2 ** (1023 - 52),
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
def test_encoding_for_Double(value):
    n = xdrlib.Double(value)
    assert n == pytest.approx(value, precision[xdrlib.Double])
    packed = struct.pack('>d', value)
    assert n.encode() == packed
    n2 = xdrlib.Double.decode(packed)
    assert n2.signbit == n.signbit
    assert n2.exponent == n.exponent
    assert n2.fraction == n.fraction


@pytest.mark.parametrize('xdrtype', [
    # xdrlib.Float,
    # xdrlib.Double,
    xdrlib.Quadruple
])
def test_maximum_value(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype.fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        max_normal_value = ctx.subtract(ctx.power(2, xdrtype.exponent_bias + 1),
                                        ctx.power(2, xdrtype.exponent_bias - xdrtype.fraction_size))
        n = xdrtype(str(max_normal_value))
        assert n.exponent == xdrtype.max_exponent - 1
        assert n.fraction == xdrtype.fraction_mask
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_subnormal(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype.fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        for i in range(xdrtype.fraction_size):
            value = ctx.power(2, - xdrtype.exponent_bias - i)
            n = xdrtype(str(value))
            fraction = 1 << (xdrtype.fraction_size - i - 1)
            packed = fraction.to_bytes(xdrtype.packed_size(), 'big')
            assert n.encode() == packed
            unpacked = xdrtype.decode(packed)
            assert n == unpacked
            assert unpacked.encode() == packed


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_smallest_normal_number(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype.fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        smallest_normal = ctx.power(2, 1 - xdrtype.exponent_bias)
        n = xdrtype(str(smallest_normal))
        assert n.exponent == 1
        assert n.fraction == 0
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_largest_subnormal_number(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype.fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        power_of_two = ctx.power(2, 1 - xdrtype.exponent_bias - xdrtype.fraction_size)
        largest_subnormal = ctx.multiply(xdrtype.fraction_mask, power_of_two)
        n = xdrtype(str(largest_subnormal))
        assert n.exponent == 0
        assert n.fraction == xdrtype.fraction_mask
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_smallest_subnormal_numbers(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype.fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        exponent = 1 - xdrtype.exponent_bias - xdrtype.fraction_size
        value = ctx.power(2, exponent)
        n = xdrtype(str(value))
        assert n.exponent == 0
        assert n.fraction == 1
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_correct_rounding_of_half_smallest_subnormal_number(xdrtype):
    with localcontext() as ctx:
        ctx.prec = xdrtype.fraction_size + 3
        ctx.rounding = ROUND_HALF_EVEN
        exponent = 1 - xdrtype.exponent_bias - xdrtype.fraction_size
        smallest_subnormal = ctx.power(2, exponent)
        n = xdrtype(str(smallest_subnormal))
        assert n.exponent == 0
        assert n.fraction == 1
        assert xdrtype.decode(n.encode()) == n


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
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
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
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
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
@pytest.mark.parametrize('value,result', [
    (3.0, True),
    (1.5, False)
])
def test_is_integer(xdrtype, value, result):
    n = xdrtype(value)
    assert n.is_integer() == result


def test_is_integer_quadruple_values():
    n = xdrlib.Quadruple('1.3545e1000')
    assert n.is_integer()


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
@pytest.mark.parametrize('hexstr,value', [
    ('0', 0.0),
    ('-0x0.0', -0.0),
    ('0x1.0000000p10', 2 ** 10),
    ('0x1.5555555555555555555555555555555555555p-2', '0.333333333333333333333333333333333333333333333333333'),
    ('-inf', '-inf'),
    ('nan', 'nan')
])
def test_fromhex(xdrtype, hexstr, value):
    if 'nan' in hexstr:
        assert math.isnan(xdrtype.fromhex(hexstr))
    elif 'inf' in hexstr:
        assert math.isinf(xdrtype.fromhex(hexstr))
    else:
        n = xdrtype.fromhex(hexstr)
        assert n == xdrtype(value)


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
@pytest.mark.parametrize('value', [
    -0.0,
    '-inf',
    -2.0,
    -3.14
])
def test_abs_value(xdrtype, value):
    n = xdrtype(value)
    m = abs(n)
    assert m == -n
    assert isinstance(m, xdrtype)
    assert m.signbit == 0
    assert m.exponent == n.exponent
    assert m.fraction == m.fraction


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
@pytest.mark.parametrize('value', [
    -0.0,
    'inf',
    '-inf',
    -2.0,
    3.14
])
def test_neg_and_pos_value(xdrtype, value):
    n = xdrtype(value)
    m = -n
    assert m == -n
    assert isinstance(m, xdrtype)
    assert m.signbit != n.signbit
    assert m.exponent == n.exponent
    assert m.fraction == m.fraction
    m = +n
    assert isinstance(m, xdrtype)
    assert m.signbit == n.signbit
    assert m.exponent == n.exponent
    assert m.fraction == m.fraction


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
@pytest.mark.parametrize('value, expected', [
    (-0.0, 0),
    (-2.5, -2),
    (3.14, 3)
])
def test_int_conversion(xdrtype, value, expected):
    n = xdrtype(value)
    assert int(n) == expected


def test_int_conversion_for_Quadruple():
    i = 2 ** 10000
    n = xdrlib.Quadruple(i)
    assert int(n) == i


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
@pytest.mark.parametrize('value,exception', [
    (float('inf'), OverflowError),
    (float('nan'), ValueError)
])
def test_int_raises_exception_for_inf_and_nan_value(xdrtype, value, exception):
    n = xdrtype(value)
    with pytest.raises(exception):
        int(n)


def test_float_conversion():
    n = xdrlib.Quadruple(2 ** 10000)
    assert math.isinf(float(n))


def test_comparison():
    n1 = xdrlib.Float(1.75)
    n2 = xdrlib.Quadruple(1.75)
    assert n1 == n2

    n1 = xdrlib.Quadruple(2 ** 10000)
    n2 = xdrlib.Quadruple(2 ** 10000)
    assert n1 == n2

    n1 = xdrlib.Quadruple(2 ** 10000)
    n2 = xdrlib.Quadruple(2 ** 10001)
    assert n1 < n2
    assert n2 > n1
    assert n1 == 2 ** 10000
    assert n2 > 2 ** 10000


# noinspection PyUnresolvedReferences
def test_real_and_imag():
    n1 = xdrlib.Quadruple(2**10000)
    assert n1.imag == 0
    assert n1.real == n1


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_float_types_cannot_be_modified(xdrtype):
    with pytest.raises(AttributeError):
        xdrtype.new_attribute = 1
    with pytest.raises(AttributeError):
        xdrtype.fraction_size = 3
    with pytest.raises(AttributeError):
        del xdrtype.exponent_bias


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float,
    xdrlib.Double,
    xdrlib.Quadruple
])
def test_optional_float_types(xdrtype):
    Opt = xdrlib.Optional(xdrtype)

    v = Opt()
    assert isinstance(v, Opt)
    assert isinstance(v, xdrlib.Void)
    assert not isinstance(v, xdrtype)
    assert v == None
    pv = b'\0\0\0\0'
    assert v.encode() == pv
    v1 = Opt.decode(pv)
    assert v1 == v
    assert v1.encode() == pv

    r = Opt('3.14')
    assert isinstance(r, Opt)
    assert isinstance(r, xdrtype)
    assert r == xdrtype('3.14')
    pr = xdrlib.TRUE.encode() + xdrtype('3.14').encode()
    assert r.encode() == pr
    r1 = Opt.decode(pr)
    assert r1 == r
    assert r1.encode() == pr


def test_anonymous_float_types():
    from xdrlib2.xdr_float import XdrFloat
    Float8 = XdrFloat(exponent_size=3, fraction_size=4)
    n = Float8(0.75)
    assert isinstance(n, Float8)
    assert isinstance(n, XdrFloat)
    assert isinstance(n, float)
    assert n == 0.75
    p = b'\x28\0\0\0'
    assert n.encode() == p
    n1 = Float8.decode(p)
    assert n1 == n
    assert n1.encode() == p

