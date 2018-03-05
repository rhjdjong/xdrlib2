# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from functools import singledispatch, reduce
import numbers
import math
import re

import struct

class _XDR_type:
    pass

class _XDR_integer(_XDR_type, int):
    _signed = None
    _min = None
    _max = None
    _packed_size = None

    def __init_subclass__(cls, size=0, signed=False, **kwargs):
        cls._signed = signed
        if signed:
            cls._min = -(1 << (size-1))
            cls._max = (1 << (size-1))
        else:
            cls._min = 0
            cls._max = 1 << size
        cls._packed_size = size // 8 + (1 if size % 8 else 0)
        super().__init_subclass__()

    def __new__(cls, value=0):
        v = super().__new__(cls, value)
        if cls._min <= v < cls._max:
            return v
        raise ValueError(f"Value {value!r} is out of range for class {cls.__name__}.\n"
                         f"\tAllowed range is [{cls._min:d} .. {cls._max - 1:d}].")

    def encode(self):
        return self.to_bytes(self._packed_size, 'big', signed=self._signed)

    @classmethod
    def decode(cls, packed):
        v = int.from_bytes(packed, 'big', signed=cls._signed)
        return cls(v)

    def __repr__(self):
        return f'{self.__class__.__name__:s}({super().__repr__():s})'


# def _fraction_bits(dec_frac, limit):
#     while dec_frac:
#         dec_frac *= 2
#         if dec_frac >= limit:
#             dec_frac -= limit
#             yield 1
#         else:
#             yield 0
#     while True:
#         yield 0
#
# def _bin_fraction_from_dec_fraction_string(fraction, bit_generator, nr_of_bits):
#     return reduce(lambda x, y: (x << 1) + y,
#                   (next(bit_generator) for _ in range(nr_of_bits)), fraction)
#
def _div_round_to_even(number, divisor):
    f, r = divmod(number, divisor)
    threshold = divisor >> 1
    if r > threshold:
        f += 1
    if r == threshold:
        f += f % 2
    return f

# @singledispatch
# def _init_float(value, self):
#     raise TypeError(f"{self.__class__.__name__:s} argument must be a string or a number, "
#                     f"not '{value.__class__.__name__:s}'")
#
# @_init_float.register(str)
# def _init_float_str(value, self):
#     self._init_from_str(value)
#
# @_init_float.register(bytes)
# def _init_float_bytes(value, self):
#     self._init_from_str(value.decode('utf8'))
#
# @_init_float.register(float)
# def _init_float_float(value, self):
#     self._init_from_number(value)
#
# @_init_float.register(int)
# def _init_float_int(value, self):
#     self._init_from_number(value)

class _XDR_float(_XDR_type, float):
    _fraction_size = None
    _fraction_mask = None
    _exponent_size = None
    _max_exponent = None
    _exponent_bias = None
    _packed_size = None
    _spec_re = re.compile(r'^[+-]?(?:(?P<inf>inf(?:inity)?)|(?P<nan>nan)(?P<payload>\d*))$')
    _nstr_pointfloat_re = re.compile(r'^[+-]?(?P<intpart>\d*)\.(?P<decpart>\d*)$')
    _nstr_exponentfloat_re = re.compile(r'^[+-]?(?P<intpart>\d*)(?:\.(?P<decpart>\d*))[Ee](?P<exp>[+-]?\d+)$')
    _hex_str_re = re.compile(r'^(?:[+-]?)(?:0x)?(?P<intpart>[0-9A-Fa-f]+)'
                             r'(?:\.(?P<fraction>[0-9A-Fa-f]+))?'
                             r'(?:p(?P<exponent>[+-]?\d+))?$')

    def __init_subclass__(cls, exponent_size=0, fraction_size=0, **kwargs):
        if exponent_size < 1:
            raise ValueError(f'Float subclass requires exponent_size >= 1, got {exponent_size:d}')
        if fraction_size < 1:
            raise ValueError(f'Float subclass requires fraction_size >= 1, got {fraction_size:d}')
        super().__init_subclass__(**kwargs)

        bit_size = 1 + exponent_size + fraction_size
        packed_size = bit_size // 8
        if bit_size != 8 * packed_size:
            raise ValueError(f'Sign bit, exponent size {exponent_size:d} and fraction size {fraction_size:d} '
                             f'together are not a multiple of 8 bits')
        cls._packed_size = packed_size

        cls._signbit_class = type('Signbit', (_XDR_integer,), {}, size=1)
        cls._exponent_class = type('Exponent', (_XDR_integer,), {}, size=exponent_size)
        cls._fraction_class = type('Fraction', (_XDR_integer,), {}, size=fraction_size)

        cls._exponent_size = exponent_size
        cls._fraction_size = fraction_size
        cls._fraction_mask = (1 << fraction_size) - 1
        cls._max_exponent = (1 << exponent_size) - 1
        cls._exponent_bias = cls._max_exponent >> 1


    def __new__(cls, *args):
        if len(args) == 3:
            signbit, exponent, fraction = args
        elif len(args) <= 1:
            arg = args[0] if args else 0.0
            if isinstance(arg, numbers.Real):
                signbit, exponent, fraction = cls._extract_from_number(arg)
            elif isinstance(arg, str):
                signbit, exponent, fraction = cls._extract_from_string(arg)
            elif isinstance(arg, bytes):
                signbit, exponent, fraction = cls._extract_from_string(arg.decode('utf8'))
            else:
                raise TypeError(f"{cls.__name__:s} argument must be a string or a number, "
                                f"not '{arg.__class__.__name__:s}'")
        else:
            raise TypeError(f"Invalid number of arguments for instantiation of '{cls.__name__:s}'")

        if exponent == cls._max_exponent:
            if fraction == 0:
                value = '-inf' if signbit else 'inf'
            else:
                value = '-nan' if signbit else 'nan'
        elif exponent == 0:
            if fraction == 0:
                value =  -0.0 if signbit else 0.0
            else:
                value = (-1 if signbit else 1) * fraction * 2**(1 - cls._exponent_bias - cls._fraction_size)
        else:
            value = (-1 if signbit else 1) * (1 + fraction * 2**(-cls._fraction_size)) * 2**(exponent - cls._exponent_bias)
        instance = super().__new__(cls, value)
        instance._frozen = False
        instance.signbit = signbit
        instance.exponent = exponent
        instance.fraction = fraction
        instance._frozen = True
        return instance

    @classmethod
    def _extract_from_number(cls, value):
        signbit = 1 if math.copysign(1.0, value) < 0 else 0
        value = abs(value)
        if math.isinf(value):
            exponent = cls._max_exponent
            fraction = 0
        elif math.isnan(value):
            exponent = cls._max_exponent
            fraction = 1 << (cls._fraction_size - 1)
        elif value == 0.0:
            exponent = 0
            fraction = 0
        else:
            if isinstance(value, numbers.Integral):
                numerator = value
                denominator = 1
            else:
                numerator, denominator = value.as_integer_ratio()
            exponent, fraction = cls._extract_from_ratio(numerator, denominator)
        return signbit, exponent, fraction

    @classmethod
    def _extract_from_string(cls, numstr):
        numstr = numstr.strip().replace('_', '')

        signbit = 1 if numstr.startswith('-') else 0

        m = cls._spec_re.match(numstr.lower())
        if m:
            exponent = cls._max_exponent
            if m['inf']:
                fraction = 0
            else:
                payload = m['payload']
                fraction = payload if payload else 1 << (cls._fraction_size - 1)
            return signbit, exponent, fraction

        m = cls._nstr_pointfloat_re.match(numstr)
        if m:
            intpart_str = m['intpart']
            decpart_str = m['decpart']
            if not intpart_str and not decpart_str:
                raise ValueError(f"could not convert string to float: '{numstr:s}'")
            dec_exp = 0
        else:
            m = cls._nstr_exponentfloat_re.match(numstr)
            if m:
                intpart_str = m['intpart']
                decpart_str = m['decpart']
                exp_str = m['exp']
                dec_exp = int(exp_str) if exp_str else 0
            else:
                raise ValueError(f"Oops. Cannot parse '{numstr:s}'. This should not happen.")

        intpart = int(intpart_str) if intpart_str else 0
        decpart = int(decpart_str) if decpart_str else 0
        if intpart == 0 and decpart == 0:
            exponent = 0
            fraction = 0
            return signbit, exponent, fraction

        if dec_exp > 0:
            intpart_str = intpart_str + decpart_str[:dec_exp] + '0'*(dec_exp - len(decpart_str))
            decpart_str = decpart_str[dec_exp:]
        elif dec_exp < 0:
            decpart_str = '0'*(-dec_exp - len(intpart_str)) + intpart_str[dec_exp:] + decpart_str
            intpart_str = intpart_str[:dec_exp]

        intpart = int(intpart_str) if intpart_str else 0
        decpart = int(decpart_str) if decpart_str else 0
        denominator = 10 ** len(decpart_str)
        exponent, fraction = cls._extract_from_ratio(denominator*intpart + decpart, denominator)
        return signbit, exponent, fraction

    @classmethod
    def _extract_from_ratio(cls, numerator, denominator):
        if numerator < denominator:
            exponent = numerator.bit_length() - denominator.bit_length()
            numerator <<= -exponent
            while numerator < denominator:
                exponent -= 1
                numerator <<= 1
            numerator -= denominator
            assert numerator < denominator
            fraction = _div_round_to_even(numerator << cls._fraction_size, denominator)
        else:
            intpart, fract_from_dec = divmod(numerator, denominator)
            exponent = intpart.bit_length() - 1
            fract_from_int = intpart & ((1 << exponent) - 1)
            fract = fract_from_int * denominator + fract_from_dec
            if exponent <= cls._fraction_size:
                fraction = _div_round_to_even(fract << (cls._fraction_size - exponent), denominator)
            else:
                fraction = _div_round_to_even(fract, denominator << (exponent - cls._fraction_size))
            if fraction.bit_length() > cls._fraction_size:
                fraction >>= 1
                exponent += 1
            assert fraction.bit_length() <= cls._fraction_size

        exponent += cls._exponent_bias
        if exponent > cls._max_exponent:
            fraction = 0
            exponent = cls._max_exponent
        if exponent <= 0:
            fraction += 1 << cls._fraction_size
            fraction >>= (1 - exponent)
            exponent = 0
        return exponent, fraction

    #
    #
    #
    # def __init__(self, *args):
    #     self._frozen = False
    #     if len(args) == 0:
    #         _init_float(0.0, self)
    #     elif len(args) == 1:
    #         _init_float(args[0], self)
    #     else: # len(args) == 3:
    #         self.signbit, self.exponent, self.fraction = args
    #     self._frozen = True
    #
    #
    # def _init_from_number(self, value):
    #     sign = math.copysign(1.0, value)
    #     self.signbit = 1 if sign < 0 else 0
    #
    #     if math.isinf(value):
    #         self.exponent = self._max_exponent
    #         self.fraction = 0
    #     elif math.isnan(value):
    #         self.exponent = self._max_exponent
    #         self.fraction = 1 << (self._fraction_size - 1)
    #     else:
    #         if isinstance(value, int):
    #             intpart = value
    #             fraction = 0
    #             n_fraction_bits = 0
    #             exp = 0
    #         else:
    #             hex_str = super().hex()
    #             m = self._hex_str_re.match(hex_str)
    #             if not m:
    #                 raise ValueError(f"Cannot parse hex float representation: '{hex_str:s}'")
    #
    #             intpart = int(m['intpart'], 16)
    #             fraction_str = m['fraction']
    #             fraction = int(fraction_str, 16) if fraction_str else 0
    #             n_fraction_bits = 4 * len(fraction_str) if fraction_str else 0
    #             exp_str = m['exponent']
    #             exp = int(exp_str) if exp_str else 0
    #
    #         if intpart == 0 and fraction == 0:
    #             self.exponent = 0
    #             self.fraction = 0
    #         else:
    #             frac_denominator = 2**self._fraction_size
    #             if intpart > 0:
    #                 bits_to_shift = intpart.bit_length() - 1
    #                 leading_fraction_part = intpart & ((1 << bits_to_shift) - 1)
    #                 fraction += leading_fraction_part << n_fraction_bits
    #                 exp += bits_to_shift
    #                 n_fraction_bits += bits_to_shift
    #
    #             if n_fraction_bits > self._fraction_size:
    #                 fraction = _div_round_to_even(fraction, 1 << (n_fraction_bits - self._fraction_size))
    #             elif n_fraction_bits < self._fraction_size:
    #                 fraction <<= self._fraction_size - n_fraction_bits
    #             if fraction >= frac_denominator:
    #                 fraction >>= 1
    #                 exp += 1
    #             self.exponent = exp + self._exponent_bias
    #             self.fraction = fraction
    #
    # def _init_from_str(self, value):
    #     value = value.strip().replace('_', '')
    #
    #     self.signbit = 1 if value.startswith('-') else 0
    #
    #     m = self._spec_re.match(value.lower())
    #     if m:
    #         self.exponent = self._max_exponent
    #         if m['inf']:
    #             self.fraction = 0
    #         else:
    #             payload = m['payload']
    #             self.fraction = payload if payload else 1 << (self._fraction_size - 1)
    #         return
    #
    #     m = self._nstr_pointfloat_re.match(value)
    #     if m:
    #         intpart_str = m['intpart']
    #         decpart_str = m['decpart']
    #         intpart = int(intpart_str) if intpart_str else 0
    #         decpart = int(decpart_str) if decpart_str else 0
    #         exp = 0
    #     else:
    #         m = self._nstr_exponentfloat_re.match(value)
    #         if m:
    #             intpart_str = m['intpart']
    #             decpart_str = m['decpart']
    #             intpart = int(intpart_str) if intpart_str else 0
    #             decpart = int(decpart_str) if decpart_str else 0
    #             exp_str = m['exp']
    #             exp = int(exp_str) if exp_str else 0
    #         else:
    #             raise ValueError(f"Oops. Cannot parse '{value:s}'. This should not happen.")
    #
    #
    #     if intpart == 0 and decpart == 0:
    #         self.exponent = 0
    #         self.fraction = 0
    #         return
    #
    #     if exp > 0:
    #         intpart_str = intpart_str + decpart_str[:exp] + '0'*(exp - len(decpart_str))
    #         decpart_str = decpart_str[exp:]
    #     elif exp < 0:
    #         decpart_str = '0'*(-exp - len(intpart_str)) + intpart_str[exp:] + decpart_str
    #         intpart_str = intpart_str[:exp]
    #
    #     intpart = int(intpart_str) if intpart_str else 0
    #     decpart = int(decpart_str) if decpart_str else 0
    #     dec_denominator = 10 ** len(decpart_str)
    #
    #     fraction = 0
    #     bin_exp = 0
    #     bin_denominator = 1 << self._fraction_size
    #     if intpart > 0:
    #         bin_exp = intpart.bit_length() - 1
    #         fraction = intpart & ((1 << bin_exp) - 1)
    #     if decpart > 0:
    #         if intpart > 0:
    #             if bin_exp < self._fraction_size:
    #                 n_bits = self._fraction_size - bin_exp
    #                 fraction += _div_round_to_even(decpart << n_bits, dec_denominator)
    #             else:
    #                 fraction = _div_round_to_even(fraction, bin_denominator)
    #         else:
    #             bin_exp = decpart.bit_length() - dec_denominator.bit_length()
    #             fraction = decpart << -bin_exp
    #             while fraction < dec_denominator:
    #                 bin_exp -= 1
    #                 fraction <<= 1
    #             fraction -= dec_denominator
    #             # fraction <<= self._fraction_size
    #             fraction = _div_round_to_even(fraction, dec_denominator)
    #     if fraction >= bin_denominator:
    #         fraction >>= 1
    #         bin_exp += 1
    #
    #     if bin_exp > self._exponent_bias:
    #         self.exponent = self._max_exponent
    #         self.fraction = 0
    #     elif bin_exp < 1 - self._exponent_bias:
    #         self.exponent = 0
    #         fraction = (1 << self._fraction_size) + fraction
    #         fraction = _div_round_to_even(fraction, 1 << (1 - self._exponent_bias - bin_exp))
    #         if fraction >= bin_denominator:
    #             fraction >>= 1
    #             self.exponent = 1
    #         self.fraction = fraction
    #     else:
    #         self.exponent = bin_exp + self._exponent_bias
    #         self.fraction = fraction

    @property
    def signbit(self):
        return self._signbit

    @signbit.setter
    def signbit(self, value):
        if self._frozen:
            raise AttributeError(f"'{self.__class__.__name__:s}' object attribute 'signbit' is read-only.")
        self._signbit = self._signbit_class(value)

    @property
    def exponent(self):
        return self._exponent

    @exponent.setter
    def exponent(self, value):
        if self._frozen:
            raise AttributeError(f"'{self.__class__.__name__:s}' object attribute 'exponent' is read-only.")
        self._exponent = self._exponent_class(value)

    @property
    def fraction(self):
        return self._fraction

    @fraction.setter
    def fraction(self, value):
        if self._frozen:
            raise AttributeError(f"'{self.__class__.__name__:s}' object attribute 'fraction' is read-only.")
        self._fraction = self._fraction_class(value)

    def encode(self):
        packed_number = self.signbit
        packed_number <<= self._exponent_size
        packed_number |= self.exponent
        packed_number <<= self._fraction_size
        packed_number |= self.fraction
        return packed_number.to_bytes(self._packed_size, 'big')

    @classmethod
    def decode(cls, packed):
        packed_integer = int.from_bytes(packed, 'big')
        fraction = packed_integer & cls._fraction_mask
        packed_integer >>= cls._fraction_size
        exponent = packed_integer & cls._max_exponent
        packed_integer >>= cls._exponent_size
        signbit = packed_integer & 1
        return cls(signbit, exponent, fraction)

    def hex(self):
        string_buffer = []
        if self.signbit == 1:
            string_buffer.append('-')
        if self.exponent == self._max_exponent:
            if self.fraction == 0:
                string_buffer.append('inf')
            else:
                string_buffer.append('nan')
        else:
            string_buffer.append('0x')
            if self.exponent == 0 and self.fraction == 0:
                string_buffer.append('0.0p+0')
            else:
                if self.exponent == 0:
                    string_buffer.append('0.')
                    exponent = 1 - self._exponent_bias
                else:
                    string_buffer.append('1.')
                    exponent = self.exponent - self._exponent_bias
                nr_of_pad_zeroes = (4 - self._fraction_size % 4) % 4
                fraction = self.fraction << nr_of_pad_zeroes
                string_buffer.append(f'{fraction:0{(self._fraction_size+3)//4}x}p')
                string_buffer.append('-' if exponent < 0 else '+')
                string_buffer.append(f'{abs(exponent):d}')
        return ''.join(string_buffer)

    def issigned(self):
        return self.signbit == 1

    def isinf(self):
        return self.exponent == self._max_exponent and self.fraction == 0

    def isnan(self):
        return self.exponent == self._max_exponent and self.fraction != 0

    def iszero(self):
        return self.exponent == 0 and self.fraction == 0

    def issubnormal(self):
        return self.exponent == 0 and self.fraction != 0
