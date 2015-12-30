'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import enum

from functools import singledispatch, update_wrapper
from collections import OrderedDict

def _methdispatch(func):
    dispatcher = singledispatch(func)
    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)
    wrapper.register = dispatcher.register
    update_wrapper(wrapper, dispatcher)
    return wrapper


block_size = 4
endian = '>'  # Big-endian format character for struct.pack


def _pack(fmt, *args):
    try:
        return struct.pack(fmt, *args)
    except struct.error as e:
        raise ValueError("Packing error") from e

def _unpack(fmt, source):
    size = struct.calcsize(fmt)
    
    try:
        tup = struct.unpack_from(fmt, source)
    except struct.error as e:
        raise ValueError("Unpacking error") from e
    
    return tup, source[size:]


def pack(obj):
    return obj._pack()

def unpack(cls, source):
    return cls._unpack(source)

def parse(cls, source):
    return cls._parse(source)

    
       
class _bounded_int(int):
    def __new__(cls, value):
        if cls._min <= value < cls._max:
            return super().__new__(cls, value)
        raise ValueError('Value out of range')


class _XdrClass:
    @classmethod
    def _unpack(cls, source):
        obj, source = cls._parse(source)
        if len(source) > 0:
            raise ValueError('Unpacking error: too much data')
        return obj

    @classmethod
    def _parse(cls, source):
        raise NotImplementedError
    
    def _pack(self):
        raise NotImplementedError
    
    
class _Atom(_XdrClass):
    def _pack(self):
        return _pack(self._packfmt, self)
    
    @classmethod
    def _parse(cls, source):
        tup, source = _unpack(cls._packfmt, source)
        return cls(tup[0]), source


class Int32(_bounded_int, _Atom):
    _max = 1<<31
    _min = -_max
    _packfmt = endian+'i'
    
def Int32Type(name):
    return type(name, (Int32,), {})

        
class Int32u(_bounded_int, _Atom):
    _max = 1<<32
    _min = 0
    _packfmt = endian+'I'

def Int32uType(name):
    return type(name, (Int32u,), {})

    
class Int64(_bounded_int, _Atom):
    _max = 1<<63
    _min = -_max
    _packfmt = endian+'q'
    
def Int64Type(name):
    return type(name, (Int64,), {})

        
class Int64u(_bounded_int, _Atom):
    _max = 1<<64
    _min = 0
    _packfmt = endian+'Q'
    
def Int64uType(name):
    return type(name, (Int64u,), {})


class Float32(float, _Atom):
    _packfmt = endian+'f'
    
def Float32Type(name):
    return type(name, (Float32,), {})

    
class Float64(float, _Atom):
    _packfmt = endian+'d'

def Float64Type(name):
    return type(name, (Float64,), {})
    

class Enumeration(Int32, enum.Enum):
    pass


def EnumerationType(name, **kwargs):
    return Enumeration(name, kwargs)


class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1
    
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE   

class _Bytes(_XdrClass, bytes):
    _packfmt = endian + '{0:d}s'
    _unpackfmt = endian + '{0:d}s{1:d}s'
    
    def __new__(cls, data):
        data_size = len(data)
        if data_size > cls._size or cls._fixed and data_size < cls._size:
            raise ValueError('Incorrect data size')
        return super().__new__(cls, data)
    
    def _pack(self):
        size = len(self)
        padded_size = ((size+block_size-1)//block_size)*block_size
        result = b''  if self._fixed else Int32u(size)._pack()
        return result + _pack(self._packfmt.format(padded_size), self)
    
    @classmethod
    def _parse(cls, source):
        if cls._fixed:
            size = cls._size
        else:
            size, source = Int32u._parse(source)
        padding = (block_size - size % block_size) % block_size
        tup, source = _unpack(cls._unpackfmt.format(size, padding), source)
        return cls(tup[0]), source
        
    
class FixedOpaque(_Bytes):
    _fixed = True

def FixedOpaqueType(name, size):
    return type(name, (FixedOpaque,), dict(_size=size))
  
class VarOpaque(_Bytes):
    _fixed = False

def VarOpaqueType(name, size):
    return type(name, (VarOpaque,), dict(_size=size))
  
class String(_Bytes):
    _fixed = False

def StringType(name, size):
    return type(name, (String,), dict(_size=size))
  

class _Array(_XdrClass, tuple):
    
    def __new__(cls, arg):
        a = tuple(arg)
        data_size = len(a)
        if data_size > cls._size or cls._fixed and data_size < cls._size:
            raise ValueError('Incorrect number of elements')
        return super().__new__(cls, (cls._element_type(x) for x in a))
    
    def _pack(self):
        result = b''  if self._fixed else Int32u(len(self))._pack()
        return result + b''.join(e._pack() for e in self)
    
    @classmethod
    def _parse(cls, source):
        if cls._fixed:
            size = cls._size
        else:
            size, source = Int32u._parse(source)
        data = []
        for _ in range(size):
            item, source = cls._element_type._parse(source)
            data.append(item)
        return cls(data), source
            

class FixedArray(_Array):
    _fixed = True
            
def FixedArrayType(name, size, element_type):
    return type(name, (FixedArray,), dict(_size=size, _element_type=element_type))

class VarArray(_Array):
    _fixed = False

def VarArrayType(name, size, element_type):
    return type(name, (VarArray,), dict(_size=size, _element_type=element_type))


class _StructureMeta(type):
    def __new__(cls, name, bases, dct):
        members = OrderedDict((n,v) for n, v in dct.items() if not n.startswith('_'))
        for n in members:
            del dct[n]
        dct['_members'] = members
        return super().__new__(cls, name, bases, dct)
    
    @classmethod
    def __prepare__(mcls, cls, bases):
        return OrderedDict()

        
class Structure(_XdrClass, metaclass=_StructureMeta):
    def __init__(self, **kwargs):
        sentinel = object()
        for name in self._members:
            setattr(self, name, sentinel)
        for n, v in kwargs.items():
            try:
                component_type = self._members[n]
            except KeyError:
                raise ValueError('Unknown structure component: {}'.format(n))
            setattr(self, n, component_type(v))
        for name in self._members:
            if getattr(self, name) is sentinel:
                raise ValueError('Missing initialization for compoenent {}'.format(name))
    
    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        for name in self._members:
            if getattr(self, name) != getattr(other, name):
                return False
        return True
    
    def _pack(self):
        return b''.join(getattr(self, n)._pack() for n in self._members)
    
    @classmethod
    def _parse(cls, source):
        result = {}
        for name, typ in cls._members.items():
            obj, source = typ._parse(source)
            result[name] = obj
        return cls(**result), source


class _UnionMeta(type):
    def __new__(cls, name, bases, dct):
        if not ('_discriminant' in dct and '_variants' in dct):
            return super().__new__(cls, name, bases, dct)
        
        discriminant_info = dct['_discriminant']
        variant_info = dct['_variants']
    
        if isinstance(discriminant_info, tuple):
            try:
                discriminant_name, discriminant_type = discriminant_info
            except ValueError:
                raise RuntimeError('Invalid name/type specification for union discriminant')
        else:
            discriminant_type = discriminant_info
            discriminant_name = discriminant_info.__name__
        if (not isinstance(discriminant_name, str) or
            not issubclass(discriminant_type, (Int32, Int32u))):
            raise RuntimeError('Invalid name/type specification for union discriminant')
        dct['_discriminant_name'] = discriminant_name
        dct['_discriminant_type'] = discriminant_type
        
        if not isinstance(variant_info, dict):
            raise RuntimeError('Invalid union variant specification (dict required)')
        
        variant_by_name = {}
        variant_by_id = {}
        for d, v in variant_info.items():
            if isinstance(v, tuple):
                try:
                    name, typ = v
                except ValueError:
                    raise RuntimeError('Invalid name/type specification for union variant {}'.format(d))
            else:
                name, typ = v.__name__, v
            if (not isinstance(name, str) or
                not issubclass(typ, _XdrClass)):
                raise RuntimeError('Invalid name/type specification for union variant {}'.format(d))
            
            if d is not None:
                try:
                    discriminant_type(d)
                except ValueError:
                    raise RuntimeError('Discriminant value {} incompatible with discriminant type'.format(d))
            variant_by_name[name] = (d, typ)
            variant_by_id[d] = (name, typ)
        dct['_variant_by_name'] = variant_by_name
        dct['_variant_by_id'] = variant_by_id
        
        return super().__new__(cls, name, bases, dct)
            
    
class Union(_XdrClass, metaclass=_UnionMeta):
    
    def __init__(self, *args, **kwargs):
        try:
            self._discriminant_name
            self._discriminant_type
            self._variant_by_name
            self._variant_by_id
        except AttributeError:
            raise NotImplementedError('Use a Union subclass with discriminant and variants specified')
        
        if len(args) + len(kwargs) > 2:
            raise ValueError("Too many arguments for union construction")
        if len(args) > 0:
            a0 = args[0]
            if isinstance(a0, str):
                variant_name = a0
                try:
                    discriminant, variant_type = self._variant_by_name[variant_name]
                except KeyError:
                    raise ValueError('Invalid variant name: {}'.format(variant_name))
            else:
                discriminant = a0
                try:
                    variant_name, variant_type = self._variant_by_id[discriminant]
                except KeyError:
                    if None in _variant_by_id:
                        variant_name, variant_type = self._variant_by_id[None]
                    else:
                        raise ValueError('Invalid discriminant value: {}'.format(discriminant))
            
                if a1 in self._variant_name
                
            discriminator = discr_type(args[0])
            variant_name, variant_type = self._variant_info(discriminator)
        else:
            try:
                discriminator = kwargs[discr_name]
            except KeyError:
                                 