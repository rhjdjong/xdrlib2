'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import enum

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
    
        
class Int32u(_bounded_int, _Atom):
    _max = 1<<32
    _min = 0
    _packfmt = endian+'I'

    
class Int64(_bounded_int, _Atom):
    _max = 1<<63
    _min = -_max
    _packfmt = endian+'q'
    
        
class Int64u(_bounded_int, _Atom):
    _max = 1<<64
    _min = 0
    _packfmt = endian+'Q'
    

class Float32(float, _Atom):
    _packfmt = endian+'f'
    
    
class Float64(float, _Atom):
    _packfmt = endian+'d'
    

class Enumeration(Int32, enum.Enum):
    pass


def enumeration(name, **kwargs):
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
    
class VarOpaque(_Bytes):
    _fixed = False

class String(_Bytes):
    _fixed = False


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
            

class VarArray(_Array):
    _fixed = False
            