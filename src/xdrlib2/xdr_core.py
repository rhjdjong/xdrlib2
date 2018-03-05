# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import math
import numbers
import re

from sys import float_info
_float_rounding = float_info.rounds

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
            cls._min = -(1 << (size - 1))
            cls._max = (1 << (size - 1))
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


def _div_round_to_even(number, divisor):
    # Precondition: positive number and divisor
    f, r = divmod(number, divisor)
    if _float_rounding == 0: # towards zero
        pass
    if _float_rounding == 1: # to nearest
        threshold = divisor >> 1
        if r > threshold:
            f += 1
        elif r == threshold:
            f += f % 2
    if _float_rounding == 2: # towards positive infinity
        if r > 0:
            f += 1
    if _float_rounding == 3: # towards negative infinity
        pass
    return f


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
    _hex_str_re = re.compile(r'^(?:0x)?(?P<intpart>[0-9a-f]+)(?:\.(?P<fraction>[0-9a-f]+))?(?:p(?P<exp>[+-]?\d+))?$')

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
                value = -0.0 if signbit else 0.0
            else:
                value = (-1 if signbit else 1) * fraction * 2 ** (1 - cls._exponent_bias - cls._fraction_size)
        else:
            try:
                value = (-1 if signbit else 1) * (1 + fraction * 2 ** (-cls._fraction_size)) \
                        * 2 ** (exponent - cls._exponent_bias)
            except OverflowError:
                value = '-inf' if signbit else 'inf'

        instance = super().__new__(cls, value)
        instance._signbit = cls._signbit_class(signbit)
        instance._exponent = cls._exponent_class(exponent)
        instance._fraction = cls._fraction_class(fraction)
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
            intpart_str = intpart_str + decpart_str[:dec_exp] + '0' * (dec_exp - len(decpart_str))
            decpart_str = decpart_str[dec_exp:]
        elif dec_exp < 0:
            decpart_str = '0' * (-dec_exp - len(intpart_str)) + intpart_str[dec_exp:] + decpart_str
            intpart_str = intpart_str[:dec_exp]

        intpart = int(intpart_str) if intpart_str else 0
        decpart = int(decpart_str) if decpart_str else 0
        denominator = 10 ** len(decpart_str)
        exponent, fraction = cls._extract_from_ratio(denominator * intpart + decpart, denominator)
        return signbit, exponent, fraction

    @classmethod
    def _extract_from_ratio(cls, numerator, denominator):
        if numerator < denominator:
            exponent = numerator.bit_length() - denominator.bit_length()
            v = numerator << -exponent
            while v < denominator:
                exponent -= 1
                v <<= 1
            assert denominator <= v < 2 * denominator
        else:
            intpart = numerator // denominator
            exponent = intpart.bit_length() - 1

        if exponent <= cls._fraction_size:
            fraction = _div_round_to_even((numerator << (cls._fraction_size - exponent)) -
                                          (denominator << cls._fraction_size), denominator)
        else:
            fraction = _div_round_to_even(numerator - (denominator << exponent),
                                          denominator << (exponent - cls._fraction_size))

        if fraction.bit_length() > cls._fraction_size:
            fraction += 1 << cls._fraction_size
            fraction >>= 1
            fraction &= cls._fraction_mask
            exponent += 1
        assert fraction.bit_length() <= cls._fraction_size

        exponent += cls._exponent_bias
        if exponent > cls._max_exponent:
            fraction = 0
            exponent = cls._max_exponent
        if exponent == 0 and fraction == cls._fraction_mask:
            fraction = 0
            exponent = 1
        if exponent <= 0:
            shift = 1 - exponent
            exponent = 0
            value = (1 << cls._fraction_size) + fraction
            fraction = _div_round_to_even(value, 1 << shift)
            if fraction.bit_length() > cls._fraction_size:
                fraction >>= 1
                exponent += 1
            assert fraction.bit_length() <= cls._fraction_size
        return exponent, fraction

    @property
    def signbit(self):
        return self._signbit

    @property
    def exponent(self):
        return self._exponent

    @property
    def fraction(self):
        return self._fraction

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

    @classmethod
    def fromhex(cls, hexstr):
        hstr = hexstr.strip().lower()
        signbit = 0
        if hstr.startswith('-'):
            signbit = 1
            hstr = hstr[1:]

        if hstr == 'inf':
            return cls(signbit, cls._max_exponent, 0)
        if hstr == 'nan':
            return cls(signbit, cls._max_exponent, 1 << (cls._fraction_size - 1))

        m = cls._hex_str_re.match(hstr)
        if not m:
            raise ValueError(f"invalid hexadecimal floating-point string '{hexstr:s}'")
        intpart = int(m['intpart'], 16)
        frac_str = m['fraction']
        frac = int(frac_str, 16) if frac_str else 0
        denominator = 1 << 4 * len(frac_str) if frac_str else 1
        numerator = intpart * denominator + frac
        exp_str = m['exp']
        exp = int(exp_str) if exp_str else 0
        if exp >= 0:
            numerator <<= exp
        else:
            denominator <<= -exp
        if numerator == 0:
            exponent, fraction = 0, 0
        else:
            exponent, fraction = cls._extract_from_ratio(numerator, denominator)
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

    def as_integer_ratio(self):
        if self.exponent == self._max_exponent:
            if self.fraction == 0:
                raise OverflowError('cannot convert Infinity to integer ratio')
            else:
                raise ValueError('cannot convert NaN to integer ratio')

        if self.exponent == 0:
            exponent = 1 - self._exponent_bias
            numerator = self.fraction
        else:
            exponent = self.exponent - self._exponent_bias
            numerator = (1 << self._fraction_size) + self.fraction
        if numerator == 0:
            return 0, 1

        denominator = (1 << self._fraction_size)
        if exponent >= 0:
            numerator <<= exponent
        else:
            denominator <<= -exponent
        factor = math.gcd(numerator, denominator)
        return numerator // factor, denominator // factor

    def is_integer(self):
        n, d = self.as_integer_ratio()
        return n % d == 0
