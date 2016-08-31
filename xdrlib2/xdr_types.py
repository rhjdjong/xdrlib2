'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import re
import inspect

from functools import singledispatch, update_wrapper
from collections import OrderedDict

from .xdr_base import block_size, endian, _is_valid_name

__all__ = ['Int32',
           'Int32u',
           'Int64',
           'Int64u',
           'Float32',
           'Float64',
           'Float128',
           'Enumeration',
           ]


def _unpack(fmt, source):
    size = struct.calcsize(fmt)
    
    try:
        tup = struct.unpack_from(fmt, source)
    except struct.error as e:
        raise ValueError("Unpacking error") from e
    
    return tup, source[size:]


class XdrObject():
    def encode(self):
        raise NotImplementedError
    
    @classmethod
    def decode(cls, source):
        obj, source = cls.parse(source)
        if len(source) > 0:
            raise ValueError('Unpacking error: too much data')
        return obj

    @classmethod
    def parse(cls, source):
        raise NotImplementedError

    @classmethod
    def make(cls, name, *args, **kwargs):
        if not isinstance(name, str) or name and not _is_valid_name(name):
            raise ValueError('Invalid name for derived class: {}'.format(name))
        return cls.__class__(name, (cls,), cls._make_class_dictionary(*args, **kwargs))
    
    
class _Atomic(XdrObject):
    def encode(self):
        return struct.pack(self._fmt, self)
    
    @classmethod
    def parse(cls, source):
        tup, source = _unpack(cls._fmt, source)
        return cls(tup[0]), source

    @classmethod
    def _make_class_dictionary(cls, *args, **kwargs):
        return {}

    
class _bounded_int(int):
    def __new__(cls, value=0):
        v = super().__new__(cls, value)
        if cls._min <= v < cls._max:
            return v
        raise ValueError('Value out of range for class {}: {}'.format(cls.__name__, v))


class _Integer(_bounded_int, _Atomic):
    pass


class _Float(float, _Atomic):
    def __new__(cls, value=0.0):
        return super().__new__(cls, value)
    
    def __init__(self, *args, **kwargs):
        super().__init__()

    
class Int32(_Integer):
    '''Representation of an XDR signed integer.
    
    Int32 is a subclass of :class:`int` that accepts values in the range [-2\ :sup:`31`\ , 2\ :sup:`31`\ -1]. Default value is 0.
    Encoded values are 4 bytes long.
    '''
    _min = -2**31
    _max = 2**31
    _fmt = endian+'i'
    
        
class Int32u(_Integer):
    '''Representation of an XDR unsigned integer.
    
    Int32u is a subclass of :class:`int` that accepts values in the range [0, 2\ :sup:`32`\ -1]. Default value is 0.
    Encoded values are 4 bytes long.
    '''
    _min = 0
    _max = 2**32
    _fmt = endian+'I'

    
class Int64(_Integer):
    '''Representation of an XDR signed hyper integer.
    
    Int64 is a subclass of :class:`int` that accepts values in the range [-2\ :sup:`63`\ , 2\ :sup:`63`\ -1]. Default value is 0.
    Encoded values are 8 bytes long.
    '''
    _min = -2**63
    _max = 2**63
    _fmt = endian+'q'


class Int64u(_Integer):
    '''Representation of an XDR unsigned hyper integer.
    
    Int64u is a subclass of :class:`int` that accepts values in the range [0, 2\ :sup:`64`\ -1]. Default value is 0.
    Encoded values are 8 bytes long.
    '''
    _min = 0
    _max = 2**64
    _fmt = endian+'Q'


class _Enumeration_meta(type):
    def __new__(cls, name, bases, dct):
        # Find the global namespace where this class is being instantiated
        frame_list = inspect.getouterframes(inspect.currentframe())
        for frame_info in frame_list:
            if frame_info.function == '<module>':
                glob = frame_info.frame.f_globals
                break
        else:
            raise RuntimeError('Cannot determine module namespace')

        members = {}
        # Retain enum definitions from the base class(es)
        for base in bases:
            if hasattr(base, '_members'):
                members.update(base._members)
        for n, v in dct.items():
            if not _is_valid_name(n): continue
            if callable(v): continue
            if isinstance(v, (classmethod, staticmethod)): continue
            if n in members:
                raise ValueError('Redefinition of enumeration name {}'.format(n))
            try:
                members[n] = Int32(v)
            except (ValueError, TypeError):
                raise ValueError('Invalid enumeration value for name {}: {}'.format(n, v))
            if n in glob:
                raise ValueError('Enumeration member name {} already present in global namespace'
                                 .format(n))
            glob[n] = v
            
        for n in members:
            try:
                del dct[n]
            except KeyError:
                pass
        dct['_members'] = members
        dct['_values'] = set(members.values())
        
        return super().__new__(cls, name, bases, dct)
    
    def __getattr__(self, name):
        try:
            return self._members[name]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'"
                             .format(self.__class__.__name__, name))

            
class Enumeration(Int32, metaclass=_Enumeration_meta):
    def __new__(cls, value=None):
        if not cls._members:
            raise NotImplementedError('Base {} class cannot be instantiated, only derived classes.'
                                      .format(cls.__class__.__name__))
        if value is None:
            value = min(cls._values)
        if value not in cls._values:
            raise ValueError("Inavlid value for '{}' object: '{}'"
                             .format(cls.__class__.__name__, value))
        return super().__new__(cls, value)
    
    @classmethod
    def _make_class_dictionary(cls, **kwargs):
        return kwargs
        
        
    
class Float32(_Float):
    '''Representation of an XDR floating-point value.
    
    Float32 is a subclass of :class:`float`. Default value is 0.0.
    Encoded values are 4 bytes long. Note that encoding a Python float
    as Float32 will in general result in loss of precision.
    '''
    _fmt = endian+'f'
    
            
class Float64(_Float):
    '''Representation of an XDR double-precision floating-point value.
    
    Float64 is a subclass of :class:`float`. Default value is 0.0.
    Encoded values are 8 bytes long. Note that encoding a Python float
    as Float32 will in general *not* result in loss of precision.
    '''
    _fmt = endian+'d'
    

class Float128(_Float):            
    '''Representation of an XDR quadruple-precision floating-point value.
    
    Float128 is a subclass of :class:`float`. Default value is 0.0.
    Encoded values are 16 bytes long.
    
    Python does not natively support quadruple-precision floating point values.
    Decoded quadruple-precision floating point values are converted into Python floats,
    which in general involves loss of precision.
    However, When decoded values are not modified, they can be encoded again without
    loss of precision.
    '''
    
    _byteorder = 'big' if endian == '>' else 'little'
    
    def __new__(cls, value=0.0):
        v = super().__new__(cls, value)
        v._encoded = b''
        return v
    
    def encode(self):
        if not self._encoded:
            # The 'struct' module does not support quadruple-precision encoding.
            # The best we can do is encode it as double-precision,
            # and reformat the packed bytes to conform to the quadruple-precicsion
            # encoding format.
            
            # First encode as double-precision, and convert the packed bytes
            # into one single integer number
            number = int.from_bytes(struct.pack(endian+'d', self), self._byteorder)

            # Extract sign, exponent, and fractional part from the packed bytestring
            # Sign bit is the leftmost bit, bit 0
            # Exponent is in the next 11 bits, bit 1 through 11
            # Fractional part is in the rightmost 52 bits, bits 12 through 63
            fraction = number & ((1<<52)-1)
            number >>= 52
            exponent = number & ((1<<11)-1)
            number >>= 11
            sign = number & 1
                
            # Ca;culate the sign, exponent, and fractional part for the quadruple-precision representation
            # Sign bit is the same
            # Exponent for double-precision is 11 bits, biased by 1023
            # Exponent for quadruple-precision is 15 bits, biased by 16383.
            # Fraction for quadruple-precision is 112 bits i.s.o. 52. Rightmost 60 bits are set to 0.
            fraction <<= 60
            
            # Handle the special cases. These are indicated by an exponent that is either all ones or all zeros.
            if exponent == 2047:
                # NaN or infinity
                exponent = 32767
            elif exponent == 0:
                # Either zero or subnormal numbers.
                if fraction:
                    # At least one non-zero bit. This is aubnormal number.
                    # The absolute value is 2**(-1022) * 0.<fraction>
                    # We need to convert this to a new exponent and fraction value
                    # such that 2**(exponent-16383) * 1.<new-fraction> has the same value.
                    
                    # First left-shift the fraction until the left-most 1 bit is in the first position.
                    shift = 0
                    while fraction & (1<111) == 0:
                        fraction <<= 1
                        shift += 1
                    # Shift one more time to get everything after the implied 1 before the fraction
                    fraction <<= 1
                    fraction &= (1<<112)-1
                    shift += 1
                    
                    # Calculate the new exponent value.
                    exponent = -1022 - shift + 16383
            else:
                # Regular number
                exponent += 16383 - 1023
                    
            # Convert again to one big number, and pack that in a 16 byte array.
            number = (sign << 127) | (exponent << 112) | fraction
            self._encoded = number.to_bytes(16, self._byteorder)
        return self._encoded

    @classmethod
    def parse(cls, source):
        # Use the first 16 bytes of the source.
        # Mimic the bahaviour of struct.unpack if there are not enough bytes.
        buf = source[:16]
        if len(buf) != 16:
            raise struct.error('unpack requires a bytes object of length 16')
        source = source[16:]
                    
        # Construct a big integer from the bytes
        number = int.from_bytes(buf, 'big')
        
        # Extract the sign, exponent, and fraction
        fraction = number & ((1<<112) - 1)
        number >>= 112
        exponent = number & ((1<<15) - 1)
        number >>= 15
        sign = number & 1
        
#         # Truncate fraction to fit in 52 bits
#         fraction >>= 60
        
        # Check for special cases
        if exponent == 32767:
            if fraction == 0:
                v = '-inf' if sign else 'inf'
            else:
                v = '-nan' if sign else 'nan'
        elif exponent == 0:
            # Either zero or subnormal.
            # But even the largeust subnormal numberin quadruple-precision
            # is to small to represent in double-precision
            v = -0.0 if sign else 0.0
        else:
            # truncate fraction to fit in 52 bits
            fraction >>= 60
            
            # Calculate exponent value for double-precision representation
            exponent = exponent - 16383 + 1023
            if exponent >= 2047:
                # Too large tp be represented in a Python float
                v = '-inf' if sign else 'inf'
            
            elif exponent <= 0:
                if exponent > -52:
                    fraction = (1 << 51) | ( fraction >> 1)
                    fraction >>= -exponent
                    v = (-1 if sign else 1) * fraction * 2**(-1022-52)
                else:
                    # Too small for a subnormal number in double-precision
                    v = -0.0 if sign else 0.0
            else:
                # This fits in a regular double-precision number
                v = (-1 if sign else 1) * ((1 << 52) | fraction) * 2**(exponent-1023-52)
        
        v = cls(v)
        v._encoded = buf
        return v, source
        
        
    
    
            
            
        