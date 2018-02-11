# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from functools import singledispatch
import re
import struct

class _XDR_type:
    pass

class _XDR_integer(_XDR_type, int):
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


class _XDR_float(_XDR_type):
    _fraction_size = None
    _exponent_size = None

    def __init_subclass__(cls, exponent_size=0, fraction_size=0, **kwargs):
        if exponent_size < 1:
            raise ValueError(f'Float subclass requires exponent_size >= 1, got {exponent_size:d}')
        if fraction_size < 1:
            raise ValueError(f'Float subclass requires fraction_size >= 1, got {fraction_size:d}')
        super().__init_subclass__(**kwargs)

        class __Signbit_class(_XDR_integer, size=1): pass
        class __Exponent_class(_XDR_integer, size=exponent_size): pass
        class __Fraction_class(_XDR_integer, size=fraction_size): pass

        cls._signbit_class = __Signbit_class
        cls._exponent_class = __Exponent_class
        cls._fraction_class = __Fraction_class

        cls._exponent_size = exponent_size
        cls._fraction_size = fraction_size
        cls._max_exponent = (1<<exponent_size) - 1
        cls._exponent_bias = cls._max_exponent >> 1
        bit_size = 1 + exponent_size + fraction_size
        cls._packed_size = bit_size // 8 + (1 if bit_size % 8 else 0)

    def __new__(cls, *args):
        if len(args) == 3:
            return cls._new_raw(*args)
        elif len(args) > 1:
            raise ValueError(f'Invalid initialisation parameters for type {cls.__name__:s}: {args!r}')
        elif len(args) == 1:
            return _XDR_float_new(args[0], cls)
        else:
            return cls._new_raw(0, 0, 0)

    @classmethod
    def _new_raw(cls, signbit, exponent, fraction):
        instance = super().__new__(cls)
        instance.signbit = signbit
        instance.exponent = exponent
        instance.fraction = fraction
        return instance

    def __repr__(self):
        return f'{self.__class__.__name__:s}({self.signbit:d}, {self.exponent:d}, {self.fraction:d})'

    def __float__(self):
        return float.fromhex(self.hex())

    def __eq__(self, other):
        return _XDR_Float_eq_obj(other, self)

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
        packed_number = (((self.signbit << self._exponent_size) | self.exponent)
                         << self._fraction_size) | self.fraction
        return packed_number.to_bytes(self._packed_size, 'big')

    @classmethod
    def decode(cls, packed):
        packed_integer = int.from_bytes(packed, 'big')
        fraction = packed_integer & ((1 << cls._fraction_size) - 1)
        packed_integer >>= cls._fraction_size
        exponent = packed_integer & ((1 << cls._exponent_size) - 1)
        packed_integer >>= cls._exponent_size
        signbit = packed_integer & 1
        return cls(signbit, exponent, fraction)

    @property
    def is_signed(self):
        return self.signbit == 1

    @property
    def is_infinite(self):
        return self.exponent == self._max_exponent and self.fraction == 0

    @property
    def is_nan(self):
        return self.exponent == self._max_exponent and self.fraction > 0

    @property
    def is_zero(self):
        return self.exponent == 0 and self.fraction == 0

    @property
    def is_subnormal(self):
        return self.exponent == 0 and self.fraction != 0

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


@singledispatch
def _XDR_float_new(arg, cls):
    raise ValueError(f'Invalid initialisation parameter for {cls.__name__:s}: {arg!r}')

@_XDR_float_new.register(float)
def _XDR_float_new_float(val, cls):
    packed_int = int.from_bytes(struct.pack('>d', val), 'big')
    fraction = packed_int & ((1 << 52) - 1)
    packed_int >>= 52
    exponent = packed_int & ((1 << 11) - 1)
    packed_int >>= 11
    signbit = packed_int & 1

    if (exponent, fraction) == (0, 0):
        return cls(signbit, 0, 0)

    if exponent == 2047:
        if fraction != 0: # NaN
            if cls._fraction_size < 52:
                fraction >>= (52 - cls._fraction_size)
                if fraction == 0:
                    fraction = 1 # Otherwise a NaN would turn into infinity
            else:
                fraction <<= (cls._fraction_size - 52)
        return cls(signbit, cls._max_exponent, fraction)


    # Subnominal numbers are the most difficult to handle.
    # We therefore first pretend that we have an infinite exponent range,
    # so that there is always an implied '1.' before the fraction.
    if exponent == 0:
        # Shift the leading 1-bit out of the fraction
        n_shift = 53 - fraction.bit_length()
        fraction <<= n_shift
        fraction &= ((1 << 52) - 1)
        real_exponent = -1022 - n_shift
    else:
        real_exponent = exponent - 1023

    # Convert the fraction and exponent to the values
    #  appropriate for the target class
    if cls._fraction_size >= 52:
        fraction <<= (cls._fraction_size - 52)
    else:
        n_shift = 52 - cls._fraction_size
        discarded_part = fraction & ((1 << n_shift) - 1)
        fraction >>= n_shift
        if discarded_part >= (1 << (n_shift - 1)):
            fraction += 1
        if fraction.bit_length() > cls._fraction_size:
            # Implied integer part would now be 2, i.e. binary 10.
            # Shift the zero back into the fraction, and adapt the exponent.
            fraction &= ((1 << cls._fraction_size) - 1)
            fraction >>= 1
            real_exponent += 1

    return _build_XDR_float_instance(cls, signbit, real_exponent, fraction)

def _build_XDR_float_instance(cls, signbit, exponent, fraction):
    target_exponent = exponent + cls._exponent_bias
    if target_exponent >= cls._max_exponent:
        # Infinite number
        return cls(signbit, cls._max_exponent, 0)
    if target_exponent <= 0:
        # Subnominal number. First move the implied 1 into the fraction
        fraction |= (1 << cls._fraction_size)
        n_shift = 1 - target_exponent  # 1 for the implied 1. The rest to bring the target exponent to 0.
        target_exponent = 0
        discarded_part = fraction & ((1 << n_shift) - 1)
        fraction >>= n_shift
        if discarded_part >= (1 << (n_shift - 1)):
            fraction += 1
        if fraction.bit_length() > cls._fraction_size:
            # Rounding caused overflow of the fraction.
            # If the target_exponent was 0, we now again have a nominal number.
            if n_shift == 1:
                fraction &= ((1 << cls._fraction_size) - 1)
                target_exponent = 1
            else:
                fraction >>= 1
        return cls(signbit, target_exponent, fraction)
    # Nominal number in target class
    return cls(signbit, target_exponent, fraction)


@_XDR_float_new.register(str)
def _XDR_float_new_string(nstr, cls):
    error_msg = f'Invalid initialiser for type {cls.__name__:s}: {nstr!r}'
    nstr = nstr.strip().replace('_', '')

    nstr_re = r'^(?P<sign>[+-]?)(?P<intpart>\d*)(?:\.(?P<fraction>\d*))?(?:[Ee](?P<exp>[+-]?\d+))?$'
    match = re.match(nstr_re, nstr)
    if match is None:
        raise ValueError(error_msg)

    signbit = 1 if match['sign'] == '-' else 0
    intpart = match['intpart']
    if intpart is None:
        intpart = ''
    fraction = match['fraction']
    if fraction is None:
        fraction = ''
    exp = match['exp']
    exp = 0 if exp is None else int(exp)

    # Short-circuit null values:
    # First strip leading zeroes from the integer part
    # and trailing zeroes from the fraction
    intpart = intpart.lstrip('0')
    fraction = fraction.rstrip('0')
    # If both intpart and fraction are now empty, we have a zero value.
    if not intpart + fraction:
        return cls(signbit, 0, 0)

    # Normalize so that exp equals 0
    if exp > 0:
        n_leftshift = min(exp, len(fraction))
        intpart += fraction[:n_leftshift]
        fraction = fraction[n_leftshift:]
        exp -= n_leftshift
        if exp > 0:
            intpart += '0'* exp
    elif exp < 0:
        exp = -exp
        n_rightshift = min(exp, len(intpart))
        fraction = intpart[-n_rightshift:] + fraction
        intpart = intpart[:-n_rightshift]
        exp -= n_rightshift
        if exp > 0:
            fraction = '0'*exp + fraction

    # At this point, <intpart>.<fraction> is the exact value represented by <nstr>,
    # with exponent (power-of-10) equal to 0.
    # Since 10**0 equals 2**0, we can now convert to binary without worrying about
    # the 2-log of the 10-exponent value.

    # First we determine the factor 2**q that will bring the value in the range from 1 to 2.
    # If intpart > 0, then this is 2**(intpart.bit_length() - 1)
    bin_exp = 0
    fraction_bits = []
    intpart_value = int(intpart) if intpart else 0
    int_bin_str = f'{intpart_value:b}'

    implied_one = intpart_value > 0
    if intpart_value > 1:  # Move all but the most significant 1-bit into the fraction
        bin_exp = len(int_bin_str) - 1
        fraction_bits.extend(int(d) for d in int_bin_str[1:])
    else:
        while not implied_one:
            fraction_bit, fraction = multiply_by_two(fraction)
            bin_exp -= 1
            if fraction_bit:
                implied_one = True

    while fraction and len(fraction_bits) < cls._fraction_size:
        fraction_bit, fraction = multiply_by_two(fraction)
        fraction_bits.append(fraction_bit)
    if len(fraction_bits) < cls._fraction_size:
        fraction_bits.extend([0]*(cls._fraction_size - len(fraction_bits)))
    else:
        fraction_bit, fraction = multiply_by_two(fraction)
        if fraction_bit:
            carry, fraction_bits = round_up(fraction_bits)
            if carry:
                fraction_bits = [0] + fraction_bits[:-1]
                bin_exp += 1

    fraction = int(''.join(str(d) for d in fraction_bits), 2)
    return _build_XDR_float_instance(cls, signbit, bin_exp, fraction)


def multiply_by_two(string):
    string = string.rstrip('0')
    if not string:
        return 0, string
    carry = 0
    digits = []
    for d in reversed(string):
        carry, new_d = divmod(2*int(d)+carry, 10)
        digits.append(new_d)
    string = ''.join(str(d) for d in reversed(digits))
    return carry, string

def round_up(bit_list):
    result = []
    carry = 1
    for d in reversed(bit_list):
        carry, new_d = divmod(d+carry, 2)
        result.append(new_d)
    return carry, list(reversed(result))


@singledispatch
def _XDR_Float_eq_obj(other, self):
    return False

@_XDR_Float_eq_obj.register(float)
def _XDR_Float_eq_float(other, self):
    return self == self.__class__(other)

@_XDR_Float_eq_obj.register(int)
def _XDR_Float_eq_int(other, self):
    if self.is_nan or self.is_infinite:
        return False
    if self.is_zero:
        return other == 0

    # Make custom _Float class that represents the integer 'other'

    other_fraction_size = other.bit_length() - 1
    other_fraction = other & ((1 << other_fraction_size) - 1)
    other_exponent = other_fraction_size
    other_exponent_size = other_fraction_size.bit_length() + 1

    class Other(_XDR_float, exponent_size=other_exponent_size, fraction_size=other_fraction_size): pass
    other_float = Other(1 if other < 0 else 0, other_exponent + OtherFloat._exponent_bias, other_fraction)
    return self == other_float


@_XDR_Float_eq_obj.register(_XDR_float)
def _XDR_Float_eq_XDR_Float(other, self):
    if other.is_nan or self.is_nan:
        return False
    if other.is_infinite or self.is_infinite:
        return self.is_infinite and other.is_infinite and other.signbit == self.signbit
    if other.is_zero or self.is_zero:
        return self.is_zero and other.is_zero
    if other.signbit != self.signbit:
        return False

    norm_fraction_size = max(self._fraction_size, other._fraction_size)
    self_exp, self_frac = normalize(self, norm_fraction_size)
    other_exp, other_frac = normalize(other, norm_fraction_size)

    return self_exp == other_exp and self_frac == other_frac

def normalize(obj, fraction_size):
    # Determine exponent and fraction as if there was an infinite exponent range

    fraction = obj.fraction
    exponent = obj.exponent - obj._exponent_bias
    if obj.exponent == 0:
        n_shift = obj._fraction_size - fraction.bit_length()
        fraction <<= 1 + n_shift  # Shift leading 1-bit out of the fraction
        fraction &= ((1 << obj._fraction_size) - 1)
        exponent -= n_shift

    # Make fraction fit in the supplied fraction_size.
    # This is always at least the current size
    fraction <<= (fraction_size - obj._fraction_size)

    return exponent, fraction
