# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrAtomic, _xdr_mode, xdr_padded, xdr_remove_padding
from .xdr_integer import XdrInteger
import numbers
import re
import math
import operator


class XdrFloat(XdrAtomic, float):
    _mode = _xdr_mode.ABSTRACT
    _final = False
    _abstract = True
    _parameters = ('exponent_size', 'fraction_size')
    _float_parameters = {}

    _spec_re = re.compile(r'^[+-]?(?:(?P<inf>inf(?:inity)?)|(?P<nan>nan)(?P<payload>\d*))$')
    _nstr_pointfloat_re = re.compile(r'^[+-]?(?P<intpart>\d*)\.(?P<decpart>\d*)$')
    _nstr_exponentfloat_re = re.compile(r'^[+-]?(?P<intpart>\d*)(?:\.(?P<decpart>\d*))[Ee](?P<exp>[+-]?\d+)$')
    _hex_str_re = re.compile(r'^(?:0x)?(?P<intpart>[0-9a-f]+)(?:\.(?P<fraction>[0-9a-f]+))?(?:p(?P<exp>[+-]?\d+))?$')

    @classmethod
    def _init_abstract_subclass_(cls, **kwargs):
        if kwargs:
            cls._float_parameters = {}
            cls._float_parameters.update(cls._float_parameters)
            for name in cls._parameters:
                if name in kwargs:
                    if name in cls._float_parameters:
                        raise TypeError(f"class '{cls.__name__:s}': redefinition of "
                                        f"class parameter '{name:s}' to {kwargs[name]!s}")
                    cls._float_parameters[name] = int(kwargs.pop(name))
            if kwargs:
                raise TypeError(f"unexpected class parameter(s) {kwargs!s} for class '{cls.__name__:s}'")
            missing_parameters = set(cls._parameters) - set(cls._float_parameters.keys())
            if missing_parameters:
                raise TypeError(f"missing class parameters {missing_parameters!s} "
                                f"for class '{cls.__name__:s}'")
            # parameters = cls._get_class_parameters(**kwargs)
            # extra_names = set(parameters.keys()) - set(cls._parameters)
            # if extra_names:
            #     raise ValueError(f"{cls.__name__:s}' subclass got unexpected parameter(s) {tuple(extra_names)!s}")
            # if cls._final:
            #     if parameters:
            #         # This is subclassing a concrete type with additional or modified parameters
            #         raise TypeError(f"cannot subclass '{cls.__name__:s}' type with modifications")
            #     return
            #
            # if cls._abstract:
            # if not all(parameters.get(n) is not None for n in cls._parameters):
            #     raise TypeError(f"incomplete instantiation of XdrInteger subclass '{cls.__name__:s}'")
            # if cls._parameters:
            exponent_size = cls.exponent_size
            fraction_size = cls.fraction_size
            if exponent_size < 1:
                raise ValueError(f'Float subclass requires exponent_size >= 1, got {exponent_size:d}')
            if fraction_size < 1:
                raise ValueError(f'Float subclass requires fraction_size >= 1, got {fraction_size:d}')
            max_exponent = (1 << exponent_size) - 1
            exponent_bias = max_exponent >> 1
            fraction_mask = (1 << fraction_size) - 1

            cls._float_parameters['exponent_size'] = exponent_size
            cls._float_parameters['fraction_size'] = fraction_size
            cls._float_parameters['max_exponent'] = max_exponent
            cls._float_parameters['exponent_bias'] = exponent_bias
            cls._float_parameters['fraction_mask'] = fraction_mask

            cls._float_parameters['signbit_class'] = XdrInteger.typedef(min=0, max=2)
            cls._float_parameters['exponent_class'] = XdrInteger.typedef(min=0, max=1<<exponent_size)
            cls._float_parameters['fraction_class'] = XdrInteger.typedef(min=0, max=1<<fraction_size)

            bit_size = 1 + exponent_size + fraction_size
            packed_size = bit_size // 8
            if bit_size != 8 * packed_size:
                raise ValueError(f'Sign bit (1), exponent size ({cls.exponent_size:d}) '
                                 f'and fraction size ({cls.fraction_size:d}) '
                                 f'together are not a multiple of 8 bits')
            cls._packed_size = packed_size
            cls._mode = _xdr_mode.FINAL

    def __new__(cls, *args, **kwargs):
        if cls._mode is _xdr_mode.ABSTRACT:
            if args:
                raise ValueError(f"Cannot instantiate abstract class {cls.__name__:s} for {args!s}")
            return cls.typedef(**kwargs)
        else:  # Concrete class instantiation
            if len(args) == 3:
                signbit, exponent, fraction = args
            elif len(args) <= 1:
                arg = args[0] if args else 0.0
                if isinstance(arg, XdrFloat):
                    signbit, exponent, fraction = cls._extract_from_xdr_instance(arg)
                elif isinstance(arg, numbers.Real):
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

            if exponent == cls.max_exponent:
                if fraction == 0:
                    value = '-inf' if signbit else 'inf'
                else:
                    value = '-nan' if signbit else 'nan'
            elif exponent == 0:
                if fraction == 0:
                    value = -0.0 if signbit else 0.0
                else:
                    value = (-1 if signbit else 1) * fraction * 2 ** (1 - cls.exponent_bias - cls.fraction_size)
            else:
                try:
                    value = (-1 if signbit else 1) * (1 + fraction * 2 ** (-cls.fraction_size)) \
                            * 2 ** (exponent - cls.exponent_bias)
                except OverflowError:
                    value = '-inf' if signbit else 'inf'

            instance = super().__new__(cls, value, **kwargs)
            instance._signbit = cls.signbit_class(signbit)
            instance._exponent = cls.exponent_class(exponent)
            instance._fraction = cls.fraction_class(fraction)
            return instance

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls._float_parameters[name]
        except KeyError:
            return super()._getattr_(name)


    def __getattr__(self, name):
        return getattr(self.__class__, name)


    @classmethod
    def _extract_from_xdr_instance(cls, value):
        signbit = value.signbit
        if value.exponent == value.max_exponent:
            exponent = cls.max_exponent
            fraction = 0 if value.fraction == 0 else 1 << (cls.fraction_size - 1)
        elif value.exponent == 0 and value.fraction == 0:
            exponent = 0
            fraction = 0
        else:
            if value.exponent == 0:
                exponent = 1 - value.exponent_bias - value.fraction_size
                coefficient = value.fraction
            else:
                exponent = value.exponent - value.exponent_bias - value.fraction_size
                coefficient = (1 << value.fraction_size) + value.fraction
            if exponent >= 0:
                numerator = coefficient << exponent
                denominator = 1
            else:
                numerator = coefficient
                denominator = 1 << -exponent
            exponent, fraction = cls._extract_from_ratio(numerator, denominator)
        return signbit, exponent, fraction

    @classmethod
    def _extract_from_number(cls, value):
        if isinstance(value, numbers.Integral):
            signbit = 1 if value < 0 else 0
        else:
            signbit = 1 if math.copysign(1.0, value) < 0 else 0
        value = abs(value)
        if not isinstance(value, numbers.Integral) and not math.isfinite(value):
            if math.isinf(value):
                exponent = cls.max_exponent
                fraction = 0
            else:  # math.isnan(value)
                exponent = cls.max_exponent
                fraction = 1 << (cls.fraction_size - 1)
        elif value == 0:
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
            exponent = cls.max_exponent
            if m['inf']:
                fraction = 0
            else:
                payload = m['payload']
                fraction = payload if payload else 1 << (cls.fraction_size - 1)
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
        exponent = numerator.bit_length() - denominator.bit_length() - 1
        while exponent < 0 and denominator <= (numerator << -(exponent + 1)):
            exponent += 1
        while exponent >= 0 and (denominator << (exponent + 1)) <= numerator:
            exponent += 1

        if exponent >= 0:
            assert (denominator << exponent) <= numerator < (denominator << (exponent + 1))
        else:
            assert denominator <= (numerator << -exponent) < (denominator << 1)
        if exponent <= -cls.exponent_bias:
            n = numerator * (1 << (cls.fraction_size + cls.exponent_bias - 1))
            d = denominator
        elif exponent <= cls.fraction_size:
            n = (numerator << (cls.fraction_size - exponent)) - (denominator << cls.fraction_size)
            d = denominator
        else:
            n = numerator - (denominator << exponent)
            d = denominator << (exponent - cls.fraction_size)

        fraction, remainder = divmod(n, d)
        if 2 * remainder > d:
            fraction += 1
        elif 2 * remainder == d:
            fraction += fraction % 2

        exponent += cls.exponent_bias
        if exponent < 0:
            exponent = 0
        if fraction.bit_length() > cls.fraction_size:
            if exponent == 0:
                exponent = 1
                fraction = 0
            else:
                fraction += (1 << cls.fraction_size)
                fraction >>= 1
                exponent += 1
        assert fraction.bit_length() <= cls.fraction_size

        if exponent > cls.max_exponent:
            fraction = 0
            exponent = cls.max_exponent
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

    @property
    def real(self):
        return self

    def encode(self):
        packed_number = self.signbit
        packed_number <<= self.exponent_size
        packed_number |= self.exponent
        packed_number <<= self.fraction_size
        packed_number |= self.fraction
        bstr = packed_number.to_bytes(self.packed_size, 'big')
        return xdr_padded(bstr)

    @classmethod
    def parse(cls, bstr):
        size = cls.packed_size
        vstr, bstr = xdr_remove_padding(bstr, size)
        packed_integer = int.from_bytes(vstr, 'big')
        fraction = packed_integer & cls.fraction_mask
        packed_integer >>= cls.fraction_size
        exponent = packed_integer & cls.max_exponent
        packed_integer >>= cls.exponent_size
        signbit = packed_integer & 1
        return cls(signbit, exponent, fraction), bstr

    @classmethod
    def fromhex(cls, hexstr):
        hstr = hexstr.strip().lower()
        signbit = 0
        if hstr.startswith('-'):
            signbit = 1
            hstr = hstr[1:]

        if hstr == 'inf':
            return cls(signbit, cls.max_exponent, 0)
        if hstr == 'nan':
            return cls(signbit, cls.max_exponent, 1 << (cls.fraction_size - 1))

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
        if self.exponent == self.max_exponent:
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
                    exponent = 1 - self.exponent_bias
                else:
                    string_buffer.append('1.')
                    exponent = self.exponent - self.exponent_bias
                nr_of_pad_zeroes = (4 - self.fraction_size % 4) % 4
                fraction = self.fraction << nr_of_pad_zeroes
                string_buffer.append(f'{fraction:0{(self.fraction_size+3)//4}x}p')
                string_buffer.append('-' if exponent < 0 else '+')
                string_buffer.append(f'{abs(exponent):d}')
        return ''.join(string_buffer)

    def as_integer_ratio(self):
        if self.exponent == self.max_exponent:
            if self.fraction == 0:
                raise OverflowError('cannot convert Infinity to integer ratio')
            else:
                raise ValueError('cannot convert NaN to integer ratio')

        if self.exponent == 0:
            exponent = 1 - self.exponent_bias
            numerator = self.fraction
        else:
            exponent = self.exponent - self.exponent_bias
            numerator = (1 << self.fraction_size) + self.fraction
        if numerator == 0:
            return 0, 1

        denominator = (1 << self.fraction_size)
        if exponent >= 0:
            numerator <<= exponent
        else:
            denominator <<= -exponent
        factor = math.gcd(numerator, denominator)
        return numerator // factor, denominator // factor

    def is_integer(self):
        n, d = self.as_integer_ratio()
        return n % d == 0

    def isinf(self):
        return self.exponent == self.max_exponent and self.fraction == 0

    def isnan(self):
        return self.exponent == self.max_exponent and self.fraction != 0

    def __repr__(self):
        return f"{self.__class__.__name__:s}({super().__repr__():s})"

    def __str__(self):
        return super().__str__()

    def __abs__(self):
        return self.__class__(0, self.exponent, self.fraction)

    def __neg__(self):
        return self.__class__(0 if self.signbit else 1, self.exponent, self.fraction)

    def __pos__(self):
        return self

    def __int__(self):
        s, e, f = self.signbit, self.exponent, self.fraction
        if e == self.max_exponent:
            if f == 0:
                raise OverflowError(f"cannot convert {self.__class__.__name__:s} infinity to integer")
            else:
                raise ValueError(f"cannot convert {self.__class__.__name__:s} NaN to integer")

        if e == 0:
            value = f >> self.exponent_bias - 1
        else:
            value = (1 << self.fraction_size) + f
            shift = e - self.exponent_bias - self.fraction_size
            if shift >= 0:
                value <<= shift
            else:
                value >>= -shift
        return -value if s else value

    def _cmp(self, other, oper):
        if self.isnan():
            return False
        if self.isinf():
            s_num = float('-inf') if self.signbit else float('inf')
            s_denom = 1
        else:
            s_num, s_denom = self.as_integer_ratio()

        if isinstance(other, numbers.Integral):
            return oper(s_num, other)

        if isinstance(other, numbers.Real):
            if math.isnan(other):
                return False
            if isinstance(other, XdrFloat) and other.isinf():
                return oper(s_num, float('-inf') if other.signbit else float('inf'))
            if math.isinf(other):
                return oper(s_num, other)
            o_num, o_denom = other.as_integer_ratio()
            return oper(s_num * o_denom, o_num * s_denom)
        else:
            return NotImplemented

    def __eq__(self, other):
        return self._cmp(other, operator.eq)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self._cmp(other, operator.lt)

    def __le__(self, other):
        return self._cmp(other, operator.le)

    def __ge__(self, other):
        return self._cmp(other, operator.ge)

    def __gt__(self, other):
        return self._cmp(other, operator.gt)


Float32 = XdrFloat.typedef('Float32', exponent_size=8, fraction_size=23)
Float = Float32


Float64 = XdrFloat.typedef('Float64', exponent_size=11, fraction_size=52)
Double = Float64


Float128 = XdrFloat.typedef('Float128', exponent_size=15, fraction_size=112)
Quadruple = Float128
