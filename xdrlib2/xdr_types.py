'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import re
import inspect
import numbers
import collections.abc

from functools import singledispatch, update_wrapper
from collections import OrderedDict, namedtuple

from .xdr_base import block_size, endian, _is_valid_name, _reserved_words, _methoddispatch

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
           'FixedArray',
           'VarArray',
           'Structure',
           'Union',
           'Optional',
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
    
    
def _unpack(fmt, size, source):
    buffer, source = _split_and_remove_padding(source, size)
    try:
        tup = struct.unpack_from(fmt, buffer)
    except struct.error as e:
        raise ValueError("Unpacking error") from e
    return tup, source

def _pad(byte_string):
    '''Pads `byte_string` with NULL bytes, to make the length a multiple of `block_size`'''
    size = len(byte_string)
    return byte_string + b'\0'*_pad_size(size)

def _pad_size(size):
    '''Return the number of NULL bytes that must be added a bytestring of length `size`'''
    return (block_size - size % block_size) % block_size

def _padded_size(size):
    return size + _pad_size(size)

def _split_and_remove_padding(byte_string, size):
    '''Returns a tuple (`a`, `b`), with `a` the leading `size` bytes from `byte_string`,
    and `b` the remainder of byte_string after `a` and any padding are removed.
    Raises `ValueError` if byte_string is too short, or if the removed padding
    contains non-NULL bytes.'''
    padded_size = _padded_size(size)
    if padded_size > len(byte_string):
        raise ValueError('Not enough data to decode')
    if any(byte_string[size:padded_size]):
        raise ValueError('Non-null bytes found in padding')
    return byte_string[:size], byte_string[padded_size:]


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
    def __new__(cls, *args, **kwargs):
        cls._check_arguments(*args, **kwargs)
        return super().__new__(cls, *args, **kwargs)

    @classmethod
    def _prepare(cls, dct):
        # This method is called  during the initialization phase of class creation.
        # Subclasses are expected to override this method to execute any
        # customization that is required for the class
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
    def _make_class_dictionary(cls, *args, **kwargs):
        return {}

    @classmethod
    def typedef(cls, name, *args, **kwargs):
        if not isinstance(name, str) or name and not _is_valid_name(name):
            raise ValueError('Invalid name for derived class: {}'.format(name))
        return cls.__class__(name, (cls,), cls._make_class_dictionary(*args, **kwargs))
    

class Void(XdrObject):
    def __new__(cls, _=None):
        return super().__new__(cls)
    
    def __init__(self, _=None):
        self._optional = False
    
    @classmethod
    def _check_arguments(cls):
        pass

    def _encode(self):
        if self._optional:
            return encode(FALSE) # @UndefinedVariable
        else:
            return b''

    @classmethod
    def _parse(cls, source):
        return cls(None), source
    
    def __eq__(self, other):
        return (other is None or isinstance(other, Void))
    

class _opt_cls(XdrObject): 
    def __new__(cls, *args, **kwargs):
        if args in ((), (None,)) and not kwargs:
            v = Void()
            v._optional = True
            return v
        return super().__new__(cls, *args, **kwargs)
    
    def _encode(self):
        return encode(TRUE) + super()._encode() # @UndefinedVariable
    
    @classmethod
    def _parse(cls, source):
        present, source = Boolean._parse(source)
        if present:
            obj, source = super()._parse(source)
            obj.__class__ = cls
        else:
            obj = Void()
            obj._optional = True
        return obj, source


def Optional(orig_cls):
    if issubclass(orig_cls, _opt_cls):
        return orig_cls
    
    if issubclass(orig_cls, Void):
        raise ValueError('Void class cannot be made optional')
    
    class new_cls(_opt_cls, orig_cls):
        pass
    new_cls.__name__ = '*'+orig_cls.__name__
    return new_cls
        

            
class _Atomic(XdrObject):
    @classmethod
    def _prepare(cls, dct):
        for name, value in dct.items():
            if name in ('min', 'max', 'fmt'):
                delattr(cls, name)
                if name == 'fmt':
                    value = endian + value
                    setattr(cls, '_encoded_size', struct.calcsize(value))
                setattr(cls, '_'+name, value)
            
    @classmethod
    def _check_arguments(cls, value):
        pass
    
    def _encode(self):
        return _pad(struct.pack(self._fmt, self))

    @classmethod
    def _parse(cls, source):
        tup, source = _unpack(cls._fmt, cls._encoded_size, source)
        return cls(tup[0]), source



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
        if not cls._values:
            raise NotImplementedError("Base class '{}' cannot be instantiated, only derived classes "
                                      'with defined enumeration members.'.format(cls.__name__))
        if value is None:
            value = min(cls._values)
        return super().__new__(cls, value)
    
    @classmethod
    def _check_arguments(cls, value):
        if not isinstance(value, numbers.Integral):
            raise ValueError("Invalid argument type '{}' for class '{}'"
                             .format(type(value), cls.__name__))
        if value not in cls._values:
            raise ValueError("Invalid value '{}' for '{}' enumeration object."
                             .format(value, cls.__name__))

    @classmethod
    def _prepare(cls, dct):
        # Consturct a dictionary of valid name, value pairs
        # from the class attributes.
        if not hasattr(cls, '_members'):
            cls._members = {}
            cls._values = set()

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

        if not members:
            # No enumeration values defined. This is either the base 'Enumeration' class
            # or the definition of an alias for an existing Enumeration class
            return
        
        if cls._members:
            raise ValueError("Cannot add new enumeration values to Enumeration subclass '{}'. "
                             "Existing values are '{}'".format(cls.__name__, cls._members))
        
        # Store the name and values in the class
        cls._values = set(members.values())  # Bootstrap with Int32 instances
        cls._members = {name: cls(value) for name, value in members.items()}
        cls._values = set(cls._members.values())  # Now make them 'cls' instances
        
        # Also make the named attributes actual 'cls' instances
        for name in members:
            setattr(cls, name, cls._members[name])

        # Determine the global (module) namespace where the Enumeration class is being created.
        # The enumerated values are added to this namespace
        stack = inspect.stack()
        
        # stack[0] is the frame where this _prepare function is executed.
        # stack[1] is the frame of the function calling this _prepare function,
        #   i.e. the __init__ of the XdrObject metaclass.
        # stack[2] is the frame where the class is created.
        for f in stack[2:]:
            # Check if this is the typedef method defined in XdrObject
            if f.function == 'typedef' and f.frame.f_globals.get('_guard') is _guard:
                continue # Try the next frame
            global_namespace = f.frame.f_globals
            break
        else:
            # Outermost caller reached.
            # Something is seriously wrong.
            raise RuntimeError('Cannot determine calling global namespace')
        
        # Add enumeration names to the global namespace
        for name, value in cls._members.items():
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
        buf, source = _split_and_remove_padding(source, 16)
                    
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

    @classmethod
    def _check_arguments(cls, value):
        if not isinstance(value, collections.abc.Sequence):
            raise ValueError("Invalid argument type '{}' for class '{}'"
                             .format(type(value), cls.__name__))

    @_methoddispatch
    def __delitem__(self, index):
        self._check_size(len(self) - 1)
        super().__delitem__(index)
    
    @__delitem__.register(slice)
    def _delslice(self, sl):
        self._check_size(len(self) - len(self[sl]))
        super().__delitem__(sl)

    def __imul__(self, number):
        self._check_size(number * len(self))
        return super().__imul__(number)
    
    def __mul__(self, number):
        self._check_size(number * len(self))
        return self.__class__(super().__mul__(number))


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
    

class FixedBytes(_FixedSequence, _Bytes):
    def __new__(cls, data=None):
        if data is None:
            data = bytes(cls._size)
        return super().__new__(cls, data)
            
    def __init__(self, data=None):
        if data is None:
            data = bytes(self._size)
        self._encoded_size = self._size
        super().__init__(data)
        
    def _encode(self):
        return _pad(bytes(self))
    
    @classmethod
    def _parse(cls, source):
        data, source = _split_and_remove_padding(source, cls._size)
        return cls(data), source
        
        
class _VarBytes(_VarSequence, _Bytes):
    def __new__(cls, data=None):
        if data is None:
            data = b''
        return super().__new__(cls, data)
            
    def __init__(self, data=None):
        if data is None:
            data = b''
        super().__init__(data)
    
    @property
    def _encoded_size(self):
        return _padded_size(Int32._encoded_size) + len(self)
    
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


class _Array(_Sequence, list):
    @classmethod
    def _prepare(cls, dct):
        for name, value in dct.items():
            if name in ('size', 'type'):
                delattr(cls, name)
                setattr(cls, '_'+ name, value)
    
    @classmethod
    def _make_class_dictionary(cls, size, type):
        return {'size': size, 'type': type}

    @_methoddispatch
    def __setitem__(self, index, value):
        super().__setitem__(index, self._type(value))
    
    @__setitem__.register(slice)
    def _setslice(self, sl, value):
        self._check_size(len(self) - len(self[sl]) + len(value))
        super().__setitem__(sl, (self._type(v) for v in value))
    
    def append(self, value):
        self._check_size(len(self) + 1)
        super().append(self._type(value))
    
    def extend(self, value):
        self._check_size(len(self) + len(value))
        super().extend(self._type(v) for v in value)
    
    def __iadd__(self, other):
        self._check_size(len(self) + len(other))
        return super().__iadd__(self._type(v) for v in other)
    
    def __add__(self, other):
        self._check_size(len(self) + len(other))
        return self.__class__(super().__add__(self._type(v) for v in other))
    

class FixedArray(_FixedSequence, _Array):
    def __new__(cls, data=None):
        if data is None:
            data = tuple(cls._type() for _ in range(cls._size))
        return super().__new__(cls, data)

    def __init__(self, data=None):
        if data is None:
            data = tuple(self._type() for _ in range(self._size))
        else:
            data = tuple(self._type(x) for x in data)
        super().__init__(data)
        
    def _encoded_size(self):
        return sum(x._encoded_size for x in self)
    
    def _encode(self):
        return b''.join(encode(x) for x in self)
    
    @classmethod
    def _parse(cls, source):
        lst = []
        for _ in range(cls._size):
            item, source = cls._type._parse(source)
            lst.append(item)
        return cls(lst), source


class VarArray(_VarSequence, _Array):
    def __new__(cls, data=[]):
        return super().__new__(cls, data)
    
    def __init__(self, data=[]):
        data = [self._type(x) for x in data]
        super().__init__(data)
    
    @property
    def _encoded_size(self):
        return _padded_size(Int32._encoded_size) + sum(x._encoded_size for x in self)
    
    def _encode(self):
        return encode(Int32u(len(self))) + b''.join(encode(x) for x in self)
    
    @classmethod
    def _parse(cls, source):
        size, source = Int32u._parse(source)
        lst = []
        for _ in range(size):
            item, source = cls._type._parse(source)
            lst.append(item)
        return cls(lst), source


class Structure(XdrObject):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)
    
    def __init__(self, *args, **kwargs):
        self._members = OrderedDict.fromkeys(self._types)
            
        if len(args) + len(kwargs) > len(self._members) :
            raise ValueError("Too many values for class '{}'".format(self.__class__.__name__))
        for name in kwargs:
            if name in tuple(self._members.keys())[:len(args)]:
                raise ValueError("Multiple values specified for member '{}' in class '{}' "
                                 .format(name, self.__class__.__name__))
            if name not in tuple(self._members.keys())[len(args):]:
                raise ValueError("Invalid member name '{}'  for class '{}'"
                                 .format(name, self.__class__.__name__))
        for (name, typ), value in zip(self._types.items(), args):
            self._members[name] = value if value.__class__ is typ else typ(value)
        for (name, value) in kwargs.items():
            typ = self._types[name]
            self._members[name] = value if value.__class__ is typ else typ(value)

    @classmethod
    def _check_arguments(cls, *args, **kwargs):
        pass
        
    @classmethod
    def _prepare(cls, dct):
        if not hasattr(cls, '_types'):
            cls._types = OrderedDict()

        member_types = OrderedDict()
        for name, value in dct.items():
            if name in member_types:
                raise ValueError("Redefinition of enumerated value for name '{}'"
                                 .format(name))
            if name in _reserved_words:
                raise ValueError("Invalid structure member name '{}' (reserved word)"
                                 .format(name))
            if _is_valid_name(name):
                if issubclass(value, XdrObject):
                    member_types[name] = value
        
        if not member_types:
            # No member elements defined. This is either the base 'Structure' class
            # or the definition of an (optioanal) alias for an existing Structure class
            return
        
        if cls._types:
            raise ValueError("Cannot add new structure members to Structure subclass '{}'")
        
        cls._types = member_types
        for name in member_types:
            delattr(cls, name)
     
    @classmethod
    def _make_class_dictionary(cls, *args):
        return OrderedDict(args)

    def _encode(self):
        return b''.join(encode(v) for v in self._members.values())

    @classmethod
    def _parse(cls, source):
        dct = {}
        for name, typ in cls._types.items():
            obj, source = typ._parse(source)
            dct[name] = obj
        return cls(**dct), source

    def __getattr__(self, name):
        try:
            return self._members[name]
        except KeyError:
            raise AttributeError("'{}' struct object has no member '{}'"
                                 .format(self.__class__.__name__, name))
    
    def __setattr__(self, name, value):
        if _is_valid_name(name):
            try:
                typ = self._types[name]
            except KeyError:
                raise AttributeError("'{}' struct object has no member '{}'"
                                     .format(self.__class__.__name__, name))
            self._members[name] = value if value.__class__ is typ else typ(value)
        else:
            super().__setattr__(name, value)
    
    def __eq__(self, other):
        if isinstance(other, (tuple, dict)):
            try:
                other = self.__class__(other)
            except ValueError:
                return False
        if type(other) != self.__class__:
            return False
        return all(x == y for x, y in zip(self._members.values(), other._members.values()))
        

_UnionTuple = namedtuple('_UnionTuple', 'switch case')

class Union(XdrObject, _UnionTuple):
    def __new__(cls, variant, *args, **kwargs):
        switch = cls._types['switch'](variant)
        case_type = cls._case_type(switch)
        value = case_type(*args, **kwargs)
        return super().__new__(cls, switch, value)
    
    @classmethod
    def _prepare(cls, dct):
        if not hasattr(cls, '_types'):
            cls._types = {}
            cls._names = {}

        data = {}
        for name in ('switch', 'case'):
            if name in dct:
                data[name] = dct[name]
                        
        if not data:
            # No union data defined. This is either the base 'Union' class
            # or the definition of an (optional) alias for an existing Union class
            return
        
        if cls._types:
            raise ValueError("Cannot add new union variants to existing Union subclass '{}'"
                             .format(cls.__name__))
        
        if not ('switch' in data and 'case' in data and data['case']):
            raise ValueError("Missing 'switch' or 'case' specification for Union class '{}'"
                             .format(cls.__name__))
        
        types = {}
        names = {}
        discr_name, discr_type = data['switch']
        if not issubclass(discr_type, (Int32, Int32u, Enumeration)):
            raise ValueError("Invalid discriminator type '{}' for Union class '{}'"
                             .format(discr_type.__name__, cls.__name__))
        types['switch'] = discr_type
        names['switch'] = discr_name
        
        for case_value, case_spec in data['case'].items():
            if case_value != 'default':
                case_value = discr_type(case_value)
            if case_spec is None:
                case_type = Void
                case_name = None
            elif isinstance(case_spec, collections.abc.Sequence) and len(case_spec) == 2:
                case_name, case_type = case_spec
            else:
                case_name, case_type = case_spec.__name__, case_spec
                
            if not issubclass(case_type, XdrObject):
                raise ValueError("Invalid type '{}' in case specification for Union class '{}', branch '{}'"
                                 .format(case_type.__name__, cls.__name__, case_value))
            
            types[case_value] = case_type
            names[case_value] = case_name
        
        cls._types = types
        cls._names = names
        
        for name in ('switch', 'case'):
            delattr(cls, name)
            
    @classmethod       
    def _case_type(cls, switch):
        c_type = cls._types.get(switch)
        if c_type is None:
            c_type = cls._types.get('default')
            if c_type is None:
                raise ValueError("Invalid switch value '{}' for Union class '{}'"
                                 .format(switch, cls.__name__))
        return c_type
        
    @classmethod
    def _check_arguments(cls, *args, **kwargs):
        pass
    
    @classmethod
    def _make_class_dictionary(cls, **kwargs):
        return kwargs

    def _encode(self):
        return encode(self.switch) + encode(self.case)
    
    @classmethod
    def _parse(cls, source):
        switch, source = cls._types['switch']._parse(source)
        case_type = cls._case_type(switch)
        case, source = case_type._parse(source)
        return cls(switch, case), source
