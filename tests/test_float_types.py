# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import pytest
import math
import struct
from decimal import Decimal, localcontext, ExtendedContext
import xdrlib2 as xdrlib

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


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
@pytest.mark.parametrize('param,value', [
    (-3.14, -3.14),
    (314, 314.0),
    ('  -3.14  ', '-3.14'),
    ('  \u0663.\u0661\u0664  ', '3.14'),
    ('\N{EM SPACE}3.14\N{EN SPACE}', '3.14')
])
def test_normal_number_encoding_and_decoding(xdrtype, param, value):
    n = xdrtype(param)
    assert isinstance(n, xdrtype)
    value = float(value)
    assert n == value
    packed = n.encode()
    m = xdrtype.decode(packed)
    assert isinstance(m, xdrtype)
    assert m.encode() == packed


@pytest.mark.parametrize('xdrtype', [
    xdrlib.Float32,
    xdrlib.Float64,
    xdrlib.Float128
])
def test_invalid_instantiation(xdrtype):
    with pytest.raises(ValueError):
        xdrtype("  0x3.1  ")
    with pytest.raises(ValueError):
        xdrtype("  -0x3.p-1  ")
    with pytest.raises(ValueError):
        xdrtype("++3.14")
    with pytest.raises(ValueError):
        xdrtype("-+3.14")
    with pytest.raises(ValueError):
        xdrtype(".nan")
    with pytest.raises(ValueError):
        xdrtype("+.inf")
    with pytest.raises(ValueError):
        xdrtype(".")
    with pytest.raises(ValueError):
        xdrtype("-.")
    with pytest.raises(TypeError) as exc_info:
        xdrtype({})
    assert "not 'dict'" in str(exc_info.value)

    # Lone surrogate
    with pytest.raises(UnicodeError):
        xdrtype('\uD8F0')

    # check that we don't accept alternate exponent markers
    with pytest.raises(ValueError):
        xdrtype("-1.7d29")
    with pytest.raises(ValueError):
        xdrtype("3D-14")

# @pytest.mark.parametrize('xdrtype', [
#     xdrlib.Float32,
#     xdrlib.Float64,
#     xdrlib.Float128
# ])
# def test_smallest_normal_number(xdrtype):
#     with localcontext(xdrtype._decimal_context) as ctx:
#         power_of_two = ctx.power(2, 1 - xdrtype._exponent_bias - xdrtype._fraction_size)
#         smallest_normal = ctx.multiply(1 << xdrtype._fraction_size, power_of_two)
#         n = xdrtype(smallest_normal)
#         assert n.exponent == 1
#         assert n.fraction == 0
#         assert xdrtype.decode(n.encode()) == n
#
# @pytest.mark.parametrize('xdrtype', [
#     xdrlib.Float32,
#     xdrlib.Float64,
#     xdrlib.Float128
# ])
# def test_largest_subnormal_number(xdrtype):
#     with localcontext(xdrtype._decimal_context) as ctx:
#         power_of_two = ctx.power(2, 1 - xdrtype._exponent_bias - xdrtype._fraction_size)
#         largest_subnormal = ctx.multiply(xdrtype._fraction_mask, power_of_two)
#         n = xdrtype(largest_subnormal)
#         assert n.exponent == 0
#         assert n.fraction == xdrtype._fraction_mask
#         assert xdrtype.decode(n.encode()) == n
#
# @pytest.mark.parametrize('xdrtype', [
#     xdrlib.Float32,
#     xdrlib.Float64,
#     xdrlib.Float128
# ])
# def test_smallest_subnormal_number(xdrtype):
#     with localcontext(xdrtype._decimal_context) as ctx:
#         power_of_two = ctx.power(2, 1 - xdrtype._exponent_bias - xdrtype._fraction_size)
#         smallest_subnormal = ctx.multiply(1, power_of_two)
#         n = xdrtype(smallest_subnormal)
#         assert n.exponent == 0
#         assert n.fraction == 1
#         assert xdrtype.decode(n.encode()) == n
#
# @pytest.mark.parametrize('xdrtype', [
#     xdrlib.Float32,
#     xdrlib.Float64,
#     xdrlib.Float128
# ])
# def test_rounding_of_half_smallest_subnormal_number(xdrtype):
#     with localcontext(xdrtype._decimal_context) as ctx:
#         power_of_two = ctx.power(2, 1 - xdrtype._exponent_bias - xdrtype._fraction_size)
#         smallest_subnormal = ctx.multiply(1, power_of_two)
#         n = xdrtype(ctx.divide(smallest_subnormal, 2))
#         assert n.exponent == 0
#         assert n.fraction == 1
#         assert xdrtype.decode(n.encode()) == n
#
# @pytest.mark.parametrize('xdrtype', [
#     xdrlib.Float32,
#     xdrlib.Float64,
#     xdrlib.Float128
# ])
# def test_less_than_half_smallest_subnormal_number_becomes_0(xdrtype):
#     with localcontext(xdrtype._decimal_context) as ctx:
#         power_of_two = ctx.power(2, 1 - xdrtype._exponent_bias - xdrtype._fraction_size)
#         smallest_subnormal = ctx.multiply(1, power_of_two)
#         n = xdrtype(ctx.divide(n, 3))
#         assert n.is_zero()
#
#
#
# examples = {
#     xdrlib.Float32: [
#         (0, 127, 0, '3f80 0000', '0x1.000000p+0'),  # 1.0
#         (1, 128, 0, 'c000 0000', '-0x1.000000p+1'),  # -2.0
#         (0, 254, 8388607, '7f7f ffff', '0x1.fffffep+127'),  # max nominal number
#         (0, 1, 0, '0080 0000', '0x1.000000p-126'),  # min nominal number
#         (1, 0, 8388607, '807f ffff', '-0x0.fffffep-126'),  # max subnominal number
#         (1, 0, 1, '8000 0001', '-0x0.000002p-126'),  # min subnominal number
#         (0, 0, 0, '0000 0000', '0x0.0p+0'),  # +0.0
#         (1, 0, 0, '8000 0000', '-0x0.0p+0'),  # -0.0
#         (0, 255, 0, '7f80 0000', 'inf'),  # +inf
#         (1, 255, 0, 'ff80 0000', '-inf'),  # -inf
#         (0, 128, 4788187, '4049 0fdb', '0x1.921fb6p+1'),  # pi
#         (0, 125, 2796203, '3eaa aaab', '0x1.555556p-2'),  # 1/3
#     ],
#     xdrlib.Float64: (
#         (0, 1023, 0, '3ff0 0000 0000 0000', '0x1.0000000000000p+0'),  # 1.0
#         (0, 1023, 1, '3ff0 0000 0000 0001', '0x1.0000000000001p+0'),  # 1.0000000000000002
#         (0, 1023, 2, '3ff0 0000 0000 0002', '0x1.0000000000002p+0'),  # 1.0000000000000004
#         (0, 1024, 0, '4000 0000 0000 0000', '0x1.0000000000000p+1'),  # 2.0
#         (1, 1024, 0, 'c000 0000 0000 0000', '-0x1.0000000000000p+1'),  # -2.0
#         (0, 1024, 0x8000000000000, '4008 0000 0000 0000', '0x1.8000000000000p+1'),  # 3.0
#         (0, 1025, 0, '4010 0000 0000 0000', '0x1.0000000000000p+2'),  # 4.0
#         (0, 1025, 0x4000000000000, '4014 0000 0000 0000', '0x1.4000000000000p+2'),  # 5.0
#         (0, 1025, 0x8000000000000, '4018 0000 0000 0000', '0x1.8000000000000p+2'),  # 6.0
#         (0, 1027, 0x7000000000000, '4037 0000 0000 0000', '0x1.7000000000000p+4'),  # 23.0
#         (0, 0, 1, '0000 0000 0000 0001', '0x0.0000000000001p-1022'),  # min subnominal number
#         (0, 0, 0xfffffffffffff, '000f ffff ffff ffff', '0x0.fffffffffffffp-1022'),  # max subnominal number
#         (0, 1, 0, '0010 0000 0000 0000', '0x1.0000000000000p-1022'),  # min nominal number
#         (0, 2046, 0xfffffffffffff, '7fef ffff ffff ffff', '0x1.fffffffffffffp+1023'),  # max nominal number
#         (0, 0, 0, '0000 0000 0000 0000', '0x0.0p+0'),  # +0.0
#         (1, 0, 0, '8000 0000 0000 0000', '-0x0.0p+0'),  # -0.0
#         (0, 2047, 0, '7ff0 0000 0000 0000', 'inf'),  # +inf
#         (1, 2047, 0, 'fff0 0000 0000 0000', '-inf'),  # -inf
#         (0, 1024, 0x921fb54442d18, '4009 21fb 5444 2d18', '0x1.921fb54442d18p+1'),  # pi
#         (0, 1021, 0x5555555555555, '3fd5 5555 5555 5555', '0x1.5555555555555p-2'),  # 1/3
#     ),
#     xdrlib.Float128: (
#         (0, 16383, 0,
#             '3fff 0000 0000 0000 0000 0000 0000 0000',
#             '0x1.0000000000000000000000000000p+0'),  # 1.0
#         (1, 16384, 0,
#             'c000 0000 0000 0000 0000 0000 0000 0000',
#             '-0x1.0000000000000000000000000000p+1'),  # -2.0
#         (0, 32766, (1 << 112) - 1,
#             '7ffe ffff ffff ffff ffff ffff ffff ffff',
#             '0x1.ffffffffffffffffffffffffffffp+16383'),  # max nominal number
#         (0, 0, 0, '0000 0000 0000 0000 0000 0000 0000 0000', '0x0.0p+0'),  # +0.0
#         (1, 0, 0, '8000 0000 0000 0000 0000 0000 0000 0000', '-0x0.0p+0'),  # -0.0
#         (0, 32767, 0, '7fff 0000 0000 0000 0000 0000 0000 0000', 'inf'),  # +inf
#         (1, 32767, 0, 'ffff 0000 0000 0000 0000 0000 0000 0000', '-inf'),  # -inf
#         (0, 16384, 2963743974480360572303246752154040,
#             '4000 921f b544 42d1 8469 898c c517 01b8',
#             '0x1.921fb54442d18469898cc51701b8p+1'),  # pi
#         (0, 16381, 0x5555555555555555555555555555,
#             '3ffd 5555 5555 5555 5555 5555 5555 5555',
#             '0x1.5555555555555555555555555555p-2'),  # 1/3
#     )
# }
#
# # binary_layout = {
# #     xdrlib.Float32: {'e': 8, 'f': 23, 'size': 4},
# #     xdrlib.Float64: {'e': 11, 'f': 52, 'size': 8},
# #     xdrlib.Float128: {'e': 15, 'f': 112, 'size': 16}
# # }
# #
#
# @pytest.mark.parametrize('xdrtype', [
#     xdrlib.Float32,
#     xdrlib.Float64,
#     xdrlib.Float128
# ])
# def test_default_instantiation(xdrtype):
#     n = xdrtype()
#     assert isinstance(n, xdrtype)
#     assert n == 0.0
#     assert n == 0
#     packed = n.encode()
#     assert len(packed) == (1 + xdrtype._exponent_size + xdrtype._fraction_size) / 8
#     assert all(b == 0 for b in packed)
#     assert xdrtype.decode(packed) == n
#
# @pytest.mark.parametrize('xdrtype', [
#     xdrlib.Float32,
#     xdrlib.Float64,
#     xdrlib.Float128
# ])
# @pytest.mark.parametrize('string,value', [
#     ('1.', 1.0),
#     ('.375', 0.375),
#     ('-2.5', -2.5),
#     ('1_2.7_5', 12.75),
#     ('-0e0', -0.0),
#     ('1.5e2', 150.0),
#     ('5e-1', 0.5),
#     ('2.e4', 20000.0),
#     ('-1.e2', -100.0)
# ])
# def test_instantiation_from_string(xdrtype, string, value):
#     n = xdrtype(string)
#     assert n == value
#
# @pytest.mark.parametrize('signbit, exponent, fraction, encoded, hex_string', [
#     *examples[xdrlib.Float32]
# ])
# def test_float32_numbers(signbit, exponent, fraction, encoded, hex_string):
#     verify_number(xdrlib.Float32, signbit, exponent, fraction, encoded, hex_string)
#
# @pytest.mark.parametrize('signbit, exponent, fraction, encoded, hex_string', [
#     *examples[xdrlib.Float64]
# ])
# def test_float64_numbers(signbit, exponent, fraction, encoded, hex_string):
#     verify_number(xdrlib.Float64, signbit, exponent, fraction, encoded, hex_string)
#
# @pytest.mark.parametrize('signbit, exponent, fraction, encoded, hex_string', [
#     *examples[xdrlib.Float128]
# ])
# def test_float128_numbers(signbit, exponent, fraction, encoded, hex_string):
#     verify_number(xdrlib.Float128, signbit, exponent, fraction, encoded, hex_string)
#
# def verify_number(xdrtype, signbit, exponent, fraction, encoded, hex_string):
#     encoded = bytes.fromhex(encoded)
#     n = xdrtype(signbit, exponent, fraction)
#     assert n.encode() == encoded
#     assert xdrtype.decode(encoded) == n
#     assert n.hex() == hex_string
#     assert n.is_signed == (signbit == 1)
#     assert n.is_zero == (exponent == 0 and fraction == 0)
#     assert n.is_subnormal == (exponent == 0 and fraction != 0)
#     assert n.is_infinite == (exponent == n._max_exponent and fraction == 0)
#
# @pytest.mark.parametrize('xdrtype,packed_pos,packed_neg', [
#     (xdrlib.Float32, '7f 80 00 00', 'ff 80 00 00'),
#     (xdrlib.Float64, '7f f0 00 00 00 00 00 00', 'ff f0 00 00 00 00 00 00'),
#     (xdrlib.Float128, '7f ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
#                       'ff ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00')
# ])
# def test_infinite_values(xdrtype, packed_pos, packed_neg):
#     pos_inf = xdrtype('inf')
#     assert pos_inf.is_infinite
#     pos_inf_packed = pos_inf.encode()
#     assert pos_inf_packed == bytes.fromhex(packed_pos)
#     assert xdrtype.decode(pos_inf_packed) == pos_inf
#
#     neg_inf = xdrtype('-inf')
#     assert pos_inf.is_infinite
#     neg_inf_packed = neg_inf.encode()
#     assert neg_inf_packed == bytes.fromhex(packed_neg)
#     assert xdrtype.decode(neg_inf_packed) == neg_inf
#
# @pytest.mark.parametrize('xdrtype,value_list', [
#     (xdrlib.Float32, (
#         ('nan', '7fc0 0000'),
#         ('-nan', 'ffc0 0000'),
#         ('nan12345', '7f80 3039'),
#         ('-nan45678', 'ff80 b26e')
#     )),
#     (xdrlib.Float64, (
#         ('nan', '7ff8 0000 0000 0000'),
#         ('-nan', 'fff8 0000 0000 0000'),
#         ('nan12345', '7ff0 0000 0000 3039'),
#         ('-nan45678', 'fff0 0000 0000 b26e')
#     )),
#     (xdrlib.Float128, (
#         ('nan', '7fff 8000 0000 0000 0000 0000 0000 0000'),
#         ('-nan', 'ffff 8000 0000 0000 0000 0000 0000 0000'),
#         ('nan12345', '7fff 0000 0000 0000 0000 0000 0000 3039'),
#         ('-nan45678', 'ffff 0000 0000 0000 0000 0000 0000 b26e')
#     ))
# ])
# def test_nan_values(xdrtype, value_list):
#     for v_str, v_hex in value_list:
#         n = xdrtype(v_str)
#         assert n.is_nan
#         packed = n.encode()
#         assert packed == bytes.fromhex(v_hex)
#         n2 = xdrtype.decode(packed)
#         assert n2.is_nan
#         assert n2.encode() == packed

# @pytest.mark.parametrize("value", [
#     2**(-1023-x) for x in range(52)
# ])
# def test_encoding_subnormal_numbers_to_quadruple_precision(value):
#     s, e, f = calculate_representation(xdrlib.Float128, value)
#     packed_data = build_packed_data(xdrlib.Float128, s, e, f)
#     x = xdrlib.Float128(value)
#     assert x.encode() == packed_data
#
#     packed_data = build_packed_data(xdrlib.Float128, 1-s, e, f)
#     x = xdrlib.Float128(-value)
#     assert x.encode() == packed_data
#
# @pytest.mark.parametrize("value", [
#     2**(-1023-x) for x in range(52)
# ])
# def test_encoding_subnormal_numbers_to_double_precision(value):
#     s, e, f = calculate_representation(xdrlib.Float64, value)
#     packed_data = build_packed_data(xdrlib.Float64, s, e, f)
#     x = xdrlib.Float64(value)
#     assert x.encode() == packed_data
#
#     packed_data = build_packed_data(xdrlib.Float64, 1-s, e, f)
#     x = xdrlib.Float64(-value)
#     assert x.encode() == packed_data
#
# @pytest.mark.parametrize("exponent, value", [
#     (15360-x, 2**(-1023-x)) for x in range(52)
# ])
# def test_decoding_quadruple_precision_numbers_to_subnormal_values(exponent, value):
#     packed_data = build_packed_data(xdrlib.Float128, 0, exponent, 0)
#     x = xdrlib.Float128.decode(packed_data)
#     assert x == value
#
#     packed_data = build_packed_data(xdrlib.Float128, 1, exponent, 0)
#     x = xdrlib.Float128.decode(packed_data)
#     assert x == -value
