'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import re
import inspect

from functools import singledispatch, update_wrapper
from collections import OrderedDict, namedtuple

from .xdr_base import block_size, endian, _is_valid_name, _reserved_words, _methoddispatch
from pip._vendor.html5lib.utils import MethodDispatcher

__all__ = ['encode',
           'decode',
           'Int32',
           'Int32u',
           'Int64',
           'Int64u',
           'Float32',
           'Float64',
           'Float128',
           'Enumeration',
           'Boolean',
           'FALSE',
           'TRUE',
           'FixedBytes',
           'VarBytes',
           'String',
           'Void',
           ]

# _guard is used by the magic that injects enumeration values in the
# global namespace where the enumeration is defined
_guard = object()


def encode(obj):
    '''Returns the XDR-encoded representation of `obj`'''
    return obj._encode()

def decode(cls, source):
    '''Decodes the XDR-encoded `source`, and returns the corresponding `cls` instance.'''
    return cls._decode(source)
    
    
def _unpack(fmt, source):
    size = struct.calcsize(fmt)
    
    try:
        tup = struct.unpack_from(fmt, source)
    except struct.error as e:
        raise ValueError("Unpacking error") from e
    
    return tup, source[size:]

def _pad(byte_string):
    '''Pads `byte_string` with NULL bytes, to make the length a multiple of `block_size`'''
    size = len(byte_string)
    return byte_string + b'\0'*_pad_size(size)

def _pad_size(size):
    '''Return the number of NULL bytes that must be added a bytestring of length `size`'''
    return (block_size - size % block_size) % block_size

def _split_and_remove_padding(byte_string, size):
    '''Returns a tuple (`a`, `b`), with `a` the leading `size` bytes from `byte_string`,
    and `b` the remainder of byte_string after `a` and any padding are removed.
    Raises `ValueError` if byte_string is too short, or if the removed padding
    contains NULL bytes.'''
    block_size = size + _pad_size(size)
    if block_size > len(byte_string):
        raise ValueError('Not enough data to decode')
    if any(byte_string[size:block_size]):
        raise ValueError('Non-null bytes found in padding')
    return byte_string[:size], byte_string[block_size:]


class _MetaXdrObject(type):
    def __init__(self, name, bases, dct):
        # Execute additional preparation actions that are necessary at class creation
        super().__init__(name, bases, dct)
        self._prepare(dct)
    
    @classmethod
    def __prepare__(mcls, cls, bases):
        # For some XDR constructs the order in which attributes are defined is important.
        # Therefore we use an OrderedDict as class __dict__
        return OrderedDict()
    
    
class XdrObject(metaclass=_MetaXdrObject):
    @classmethod
    def _prepare(cls, dct):
        # This method during the intitalization of class creation.
        # Subclasses are expected to override this to execute any
        # setup that is required for the class.
        pass
    
    def _encode(self):
        raise NotImplementedError
    
    @classmethod
    def _decode(cls, source):
        obj, source = cls._parse(source)
        if len(source) > 0:
            raise ValueError('Unpacking error: too much data')
        return obj

    @classmethod
    def _parse(cls, source):
        raise NotImplementedError

    @classmethod
    def typedef(cls, name, *args, **kwargs):
        if not isinstance(name, str) or name and not _is_valid_name(name):
            raise ValueError('Invalid name for derived class: {}'.format(name))
        return cls.__class__(name, (cls,), cls._make_class_dictionary(*args, **kwargs))
    

class Void(XdrObject):
    def __new__(cls, _=None):
        return super().__new__(cls)
    
    def _encode(self):
        return b''
    
    @classmethod
    def _parse(cls, source):
        return cls(None), source
    
    def __eq__(self, other):
        return (other is None or isinstance(other, Void))
    
       
class _Atomic(XdrObject):
    @classmethod
    def _prepare(cls, dct):
        for name, value in dct.items():
            if name in ('min', 'max', 'fmt'):
                delattr(cls, name)
                if name == 'fmt':
                    value = endian + value
                    setattr(cls, '_size', struct.calcsize(value))
                setattr(cls, '_'+name, value)

    def _encode(self):
        return _pad(struct.pack(self._fmt, self))
    
    @classmethod
    def _parse(cls, source):
        data, source = _split_and_remove_padding(source, cls._size)
        tup, data = _unpack(cls._fmt, data)
        if data:
            raise ValueError('Too much data')
        return cls(tup[0]), source

    @classmethod
    def _make_class_dictionary(cls, *args, **kwargs):
        return {}


class _Integer(_Atomic, int):
    def __new__(cls, value=0):
        v = super().__new__(cls, value)
        if cls._min <= v < cls._max:
            return v
        raise ValueError('Value out of range for class {}: {}'.format(cls.__name__, v))


class _Float(_Atomic, float):
    def __new__(cls, value=0.0):
        return super().__new__(cls, value)
    

    
class Int32(_Integer):
    '''Representation of an XDR signed integer.
    
    Int32 is a subclass of :class:`int` that accepts values in the range [-2\ :sup:`31`\ , 2\ :sup:`31`\ -1]. Default value is 0.
    Encoded values are 4 bytes long.
    '''
    min = -2**31
    max = 2**31
    fmt = 'i'
    
        
class Int32u(_Integer):
    '''Representation of an XDR unsigned integer.
    
    Int32u is a subclass of :class:`int` that accepts values in the range [0, 2\ :sup:`32`\ -1]. Default value is 0.
    Encoded values are 4 bytes long.
    '''
    min = 0
    max = 2**32
    fmt = 'I'

    
class Int64(_Integer):
    '''Representation of an XDR signed hyper integer.
    
    Int64 is a subclass of :class:`int` that accepts values in the range [-2\ :sup:`63`\ , 2\ :sup:`63`\ -1]. Default value is 0.
    Encoded values are 8 bytes long.
    '''
    min = -2**63
    max = 2**63
    fmt = 'q'


class Int64u(_Integer):
    '''Representation of an XDR unsigned hyper integer.
    
    Int64u is a subclass of :class:`int` that accepts values in the range [0, 2\ :sup:`64`\ -1]. Default value is 0.
    Encoded values are 8 bytes long.
    '''
    min = 0
    max = 2**64
    fmt = 'Q'


            
class Enumeration(Int32):
    '''Abstract base class for XDR enumerations.
    
    Enumeration is a subclass of :class:`Int32`.
    It is an abstract class, and must itself be subclassed to obtain concrete enumeration classes.
    Enumerated names and values are defined as attributes of the derived class.
    These names are also injected in the global (module) namespace where
    the derived class is defined.
    Enumeration classes can be instantiated with a value that corresponds with
    one of the named values defined in the enumeration. Default value is the
    lowest enumerated value defined for the class.
    Enumeration values are encoded as :class:`Int32` values, and are 4 bytes long.
    '''
    def __new__(cls, value=None):
        if not cls._members:
            raise NotImplementedError('Base {} class cannot be instantiated, only derived classes.'
                                      .format(cls.__name__))
        if value is None:
            value = min(cls._values)
        else:
            value = super().__new__(cls, value)
        if value not in cls._values:
            raise ValueError("Inavlid value for '{}' enumeration object: '{}'"
                             .format(cls.__name__, value))
        return value
    
    @classmethod
    def _prepare(cls, dct):
        # Consturct a dictionary of valid name, value pairs
        # from the class attributes.
        members = {}
        for name, value in dct.items():
            if name in members:
                raise ValueError("Redefinition of enumerated value for name '{}'"
                                 .format(name))
            if name in _reserved_words:
                raise ValueError("Invalid enumeration value name '{}' (reserved word)"
                                 .format(name))
            if _is_valid_name(name):
                if callable(value): continue
                if isinstance(value, (classmethod, staticmethod)): continue
                try:
                    value = Int32(value)
                except (ValueError, TypeError):
                    raise ValueError("Invalid enumeration value '{}' for name '{}'"
                                     .format(value, name))
                members[name] = value

        if members and cls._members:
            raise ValueError('Cannot add new enumeration values to existing Enumeration subclass')
        
        # Store the name and values in the class
        # We need to have something in _members and _values, otherwise
        # the class cannot be instantiated
        cls._members = members
        cls._values = set(members.values())
        
        # Now ensure that the values are really instances of this class
        for name, value in members.items():
            members[name] = cls(value)
        cls._values = set(members.values())
        
        
        # Determine the global (module) namespace where the Enumeration class is being created.
        # The enumerated values are added to this namespace
        stack = inspect.stack()
        
        # stack[0] is the frame where this _prepare function is executed.
        # stack[1] is the frame of the function calling this _prepare function,
        #   i.e. the __init__ of the XdrObject metaclass.
        # stack[2] is the frame where the class is created.
        for f in stack[2:]:
            # Check if this is the typedef method defined in XdrObject
            if f.function == '<module>':
#                 if f.function == 'typedef' and f.frame.f_globals.get('_guard') is _guard:
#                     continue # Try the next frame
                global_namespace = f.frame.f_globals
                break
        else:
            # Outermost caller reached without encountering a '<module>'.
            # Something is seriously wrong.
            raise RuntimeError('Cannot determine calling global namespace')
        
        # Add enumeration names to the global namespace
        for name, value in members.items():
            if name in global_namespace:
                raise ValueError('Name conflict. Enumeration name {} already exists.'
                                 .format(name))
            global_namespace[name] = value
            


    @classmethod
    def _make_class_dictionary(cls, **kwargs):
        return kwargs
        

class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1
            
    
class Float32(_Float):
    '''Representation of an XDR floating-point value.
    
    Float32 is a subclass of :class:`float`. Default value is 0.0.
    Encoded values are 4 bytes long. Note that encoding a Python float
    as Float32 will in general result in loss of precision.
    '''
    fmt = 'f'
    
            
class Float64(_Float):
    '''Representation of an XDR double-precision floating-point value.
    
    Float64 is a subclass of :class:`float`. Default value is 0.0.
    Encoded values are 8 bytes long. Note that encoding a Python float
    as Float32 will in general *not* result in loss of precision.
    '''
    fmt = 'd'
    

class Float128(_Float):            
    '''Representation of an XDR quadruple-precision floating-point value.
    
    Float128 is a subclass of :class:`float`. Default value is 0.0.
    Encoded values are 16 bytes long.
    
    Python does not natively support quadruple-precision floating point values.
    Decoded quadruple-precision floating point values are converted into Python floats,
    which in general involves loss of precision.
    However, when decoded values are not modified, they can be encoded again without
    loss of precision.
    '''
    
    fmt = 'd'   # 
    _byteorder = 'big' if endian == '>' else 'little'
    
    def __new__(cls, value=0.0):
        v = super().__new__(cls, value)
        v._encoded = b''
        return v
    
    def _encode(self):
        if not self._encoded:
            # The 'struct' module does not support quadruple-precision encoding.
            # The best we can do is encode it as double-precision,
            # and reformat the packed bytes to conform to the quadruple-precicsion
            # encoding format.
            
            # First encode as double-precision, and convert the packed bytes
            # into one single integer number
            number = int.from_bytes(struct.pack(self._fmt, self), self._byteorder)

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
                        
            # Handle the special cases. These are indicated by an exponent that is either all ones or all zeros.
            if exponent == 2047:
                # NaN or infinity
                exponent = 32767
                # Fraction for quadruple-precision is 112 bits i.s.o. 52. Rightmost 60 bits are set to 0.
                fraction <<= 60

            elif exponent == 0:
                # Either zero or subnormal numbers.
                if fraction:
                    # At least one non-zero bit. This is aubnormal number.
                    # The absolute value is 2**(-1022) * 0.<fraction>.
                    # or equivalently 2**(-1022) * fraction * 2**(-52)
                    # We need to convert this to a new exponent and fraction value
                    # such that 2**(exponent-16383) * 1.<new-fraction> has the same value.
                    
                    # Fraction for quadruple-precision is 112 bits i.s.o. 52.
                    # Start by setting the rightmost 60 bits are set to 0.
                    fraction <<= 60
                    # The absolute value is now 2**(-1022) * fraction * 2**(-112)
                    
                    # Now left-shift the fraction until the left-most 1 bit is in the first position.
                    shift = 0
                    while fraction & (1<111) == 0:
                        fraction <<= 1
                        shift += 1
                        # The absolute value is now 2**(-1022) * fraction * 2**(-112-shift)

                    # Shift one more time to get everything after the fraction that follows the implied 1.
                    fraction <<= 1
                    fraction &= (1<<112)-1
                    shift += 1
                    # The absolute value is now 2**(-1022) * (1 + fraction * 2**(-112)) * 2**(-shift)
                    # or equivalently 2**(-1022-shift) * (1 + fraction * 2**(-112))

                    # Calculate the new exponent value, biased by 16383.
                    exponent = -1022 - shift + 16383
            else:
                # Regular number. Absolute value is 2**(exponent-1023) * (1 + fraction * 2**(-52))
                
                # Fraction for quadruple-precision is 112 bits i.s.o. 52. Rightmost 60 bits are set to 0.
                fraction <<= 60
                # Absolute value is now 2**(exponent-1023) * (1 + fraction * 2**(-112))
                # or 2**(exponent - 1023 + 16383 - 16383) * (1 + fraction * 2**(-112))
                
                # Calculate the quadruple precision exponent
                exponent = exponent - 1023 + 16383
                    
            # Convert again to one big number, and pack that in a 16 byte array.
            number = (sign << 127) | (exponent << 112) | fraction
            self._encoded = number.to_bytes(16, self._byteorder)
        return _pad(self._encoded)

    @classmethod
    def _parse(cls, source):
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
        

class _Sequence(XdrObject):
    def __init__(self, data):
        self._check_size(len(data))
        super().__init__(data)

    @_methoddispatch
    def __delitem__(self, index):
        self._check_size(len(self) - 1)
        super().__delitem__(index)
    
    @__delitem__.register(slice)
    def _delslice(self, sl):
        self._check_size(len(self) - len(self[sl]))
        super().__delitem__(sl)


class _FixedSequence(_Sequence):
    @classmethod
    def _check_size(cls, size):
        if size != cls._size:
            raise(ValueError("Incorrect size '{}' for '{}' object. Expected '{}'."
                             .format(size, cls.__name__, cls._size)))

class _VarSequence(_Sequence):
    @classmethod
    def _check_size(cls, size):
        if size > cls._size:
            raise(ValueError("Size '{}' lo large for '{}' object. Must be at most '{}'."
                             .format(size, cls.__name__, cls._size)))
            
    
class _Bytes(_Sequence, bytearray):
    @classmethod
    def _prepare(cls, dct):
        for name, value in dct.items():
            if name in ('size'):
                delattr(cls, name)
                setattr(cls, '_'+ name, value)

    @classmethod
    def _make_class_dictionary(cls, size):
        return {'size': size}

    @_methoddispatch
    def __setitem__(self, index, value):
        super().__setitem__(index, value)
    
    @__setitem__.register(slice)
    def _setslice(self, sl, value):
        self._check_size(len(self) - len(self[sl]) + len(value))
        super().__setitem__(sl, value)
    
    def append(self, value):
        self._check_size(len(self) + 1)
        super().append(value)
    
    def extend(self, value):
        self._check_size(len(self) + len(value))
        super().extend(value)
    
    def __iadd__(self, other):
        self._check_size(len(self) + len(other))
        return super().__iadd__(other)
    
    def __add__(self, other):
        self._check_size(len(self) + len(other))
        return self.__class__(super().__add__(other))
    
    def __imul__(self, number):
        self._check_size(number * len(self))
        return super().__imul__(number)
    
    def __mul__(self, number):
        self._check_size(number * len(self))
        return self.__class__(super().__mul__(number))


class FixedBytes(_FixedSequence, _Bytes):
    def __init__(self, data=None):
        if data is None:
            data = bytes(self._size)
        super().__init__(data)
        
    def _encode(self):
        return _pad(bytes(self))
    
    @classmethod
    def _parse(cls, source):
        data, source = _split_and_remove_padding(source, cls._size)
        return cls(data), source
        
        
class _VarBytes(_VarSequence, _Bytes):
    def __init__(self, data=None):
        if data is None:
            data = b''
        super().__init__(data)
    
    def _encode(self):
        return encode(Int32u(len(self))) + _pad(bytes(self))
    
    @classmethod
    def _parse(cls, source):
        size, source = Int32u._parse(source)
        data, source = _split_and_remove_padding(source, size)
        return cls(data), source
    
class VarBytes(_VarBytes):
    pass

class String(_VarBytes):
    pass


        