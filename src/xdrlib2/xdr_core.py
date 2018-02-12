# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from functools import singledispatch, reduce
import math
from decimal import Decimal, localcontext, DefaultContext, InvalidOperation, ROUND_HALF_EVEN
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
        return f'{self.__class__.__name__:s}({super().__repr__(self):s})'


class _XDR_float(_XDR_type, Decimal):
    _fraction_size = None
    _exponent_size = None
    _max_exponent = None
    _exponent_bias = None
    _packed_size = None
    _decimal_precision = None

    def __init_subclass__(cls, exponent_size=0, fraction_size=0, **kwargs):
        if exponent_size < 1:
            raise ValueError(f'Float subclass requires exponent_size >= 1, got {exponent_size:d}')
        if fraction_size < 1:
            raise ValueError(f'Float subclass requires fraction_size >= 1, got {fraction_size:d}')
        super().__init_subclass__(**kwargs)

        cls._signbit_class = type('Signbit', (_XDR_integer,), {}, size=1)
        cls._exponent_class = type('Exponent', (_XDR_integer,), {}, size=exponent_size)
        cls._fraction_class = type('Fraction', (_XDR_integer,), {}, size=fraction_size)

        cls._exponent_size = exponent_size
        cls._fraction_size = fraction_size
        cls._fraction_mask = (1 << fraction_size) - 1
        cls._max_exponent = (1 << exponent_size) - 1
        cls._exponent_bias = cls._max_exponent >> 1
        bit_size = 1 + exponent_size + fraction_size
        cls._packed_size = bit_size // 8 + (1 if bit_size % 8 else 0)
        cls._decimal_precision = 1 + math.ceil(fraction_size * math.log10(2.0))
        with localcontext(DefaultContext) as ctx:
            ctx.prec = cls._decimal_precision
            ctx.rounding = ROUND_HALF_EVEN
            cls._log2 = Decimal('2.0').log10()


    def __new__(cls, value=0):
        value_error_msg = f'could not convert {value.__class__.__name__:s} to {cls.__name__:s}: {value!r}'
        type_error_msg = f'conversion from {value.__class__.__name__:s} to {cls.__name__:s} is not supported'

        with localcontext(DefaultContext) as ctx:
            ctx.prec = cls._decimal_precision
            ctx.rounding = ROUND_HALF_EVEN

            if isinstance(value, tuple):
                signbit, exponent, fraction = value
                sign_str = f'{"-" if signbit else ""}'
                if exponent == cls._max_exponent:
                    if fraction == 0:
                        instance = super().__new__(cls, f'{sign_str:s}Infinity')
                    else:
                        instance = super().__new__(cls, f'{sign_str:s}NaN{fraction:d}')
                elif exponent == 0:
                    if fraction == 0:
                        instance = super().__new__(cls, f'{sign_str:s}0.0')
                    else:
                        instance = (Decimal(f'{sign_str:s}{fraction:d}')
                            * (Decimal(2) ** Decimal(1-cls._exponent_bias)))
                else:
                    instance = (Decimal(f'{sign_str:s}1{fraction:d}')
                        * (Decimal(2) ** Decimal(exponent - cls._exponent_bias)))
            else:
                # Catch unicode errors
                if isinstance(value, str):
                    value = value.encode('utf8').decode('utf8')
                try:
                    instance = super().__new__(cls, value)
                except TypeError:
                    raise TypeError(type_error_msg)
                except InvalidOperation:
                    raise ValueError(value_error_msg)
                signbit = 1 if instance.is_signed() else 0
                sign_str = f'{"-" if signbit else ""}'

                if instance.is_infinite():
                    exponent = cls._max_exponent
                    fraction = 0
                elif instance.is_nan():
                    exponent = 0
                    fraction = reduce(lambda x, y: 10*x + y, instance.as_tuple().digits, 0) & cls._fraction_mask
                elif instance.is_zero():
                    exponent = 0
                    fraction = 0
                else:
                    # Calculate exponent and mantissa such that
                    # instance == mantissa * 2**exponent with 1 <= mantissa < 2
                    exponent = math.floor(abs(instance.log10()/cls._log2))
                    mantissa = instance * (Decimal(2) ** Decimal(-exponent))
                    if exponent > cls._exponent_bias:
                        # Overflow --> infinite
                        instance = super().__new__(cls, ('{sign_str:s}Infinity'))
                        exponent = cls._max_exponent
                        fraction = 0
                    else:
                        if 1 - cls._exponent_bias <= exponent <= cls._exponent_bias:
                            # Nominal number
                            exponent = exponent + cls._exponent_bias
                            fraction = round(mantissa * Decimal(2**cls._fraction_size)) & cls._fraction_mask
                        else:
                            # Subnominal or underflow
                            exponent = 0
                            exponent_delta = 1 - cls._exponent_bias - exponent
                            if exponent_delta <= cls._fraction_size:
                                # Subnominal
                                fraction = round(mantissa * Decimal(2**(cls._fraction_size - exponent_delta)))
                            else:
                                # Underflow
                                fraction = 0

        instance.signbit = signbit
        instance.exponent = exponent
        instance.fraction = fraction
        return instance

    @property
    def signbit(self):
        return self._signbit

    @signbit.setter
    def signbit(self, value):
        self._signbit = self._signbit_class(value)

    @property
    def exponent(self):
        return self._exponent

    @exponent.setter
    def exponent(self, value):
        self._exponent = self._exponent_class(value)

    @property
    def fraction(self):
        return self._fraction

    @fraction.setter
    def fraction(self, value):
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
        return cls((signbit, exponent, fraction))

    def hex(self):
        shift_size = {0: 0, 1: 3, 2: 2, 3: 1}[self._fraction_size % 4]
        fraction = self.fraction << shift_size
        string_buffer = []
        if self.is_signed:
            string_buffer.append('-')
        if self.is_infinite:
            string_buffer.append('inf')
        elif self.is_nan:
            string_buffer.append('nan')
        else:
            string_buffer.append('0x')
            if self.is_zero:
                string_buffer.append('0.0p+0')
            else:
                if self.is_subnormal:
                    string_buffer.append('0.')
                    exponent = -self._exponent_bias + 1
                else:
                    string_buffer.append('1.')
                    exponent = self.exponent - self._exponent_bias
                string_buffer.append(f'{fraction:0{(self._fraction_size+3)//4}x}p')
                string_buffer.append('-' if exponent < 0 else '+')
                string_buffer.append(f'{abs(exponent):d}')
        return ''.join(string_buffer)
