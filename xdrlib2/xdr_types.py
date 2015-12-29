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

    
class _bounded_int(int):
    def __new__(cls, value):
        if cls.min <= value < cls.max:
            return super().__new__(cls, value)
        raise ValueError('Value out of range')

class _packable:    
    def pack(self):
        return _pack(self.packfmt, self) # + self.padding
    
    @classmethod
    def unpack(cls, source):
        obj, source = cls.parse(source)
        if len(source) > 0:
            raise ValueError('Unpacking error: too much data')
        return obj
    
    @classmethod
    def parse(cls, source):
        tup, source = _unpack(cls.packfmt, source)
        return cls(tup[0]), source


class _XdrClass:
    @classmethod
    def unpack(cls, source):
        obj, source = cls.parse(source)
        if len(source) > 0:
            raise ValueError('Unpacking error: too much data')
        return obj

    
class _Atom(_XdrClass):
    def pack(self):
        return _pack(self.packfmt, self)
    
    @classmethod
    def parse(cls, source):
        tup, source = _unpack(cls.packfmt, source)
        return cls(tup[0]), source


class Int32(_bounded_int, _Atom):
    max = 1<<31
    min = -max
    packfmt = endian+'i'
    
        
class Int32u(_bounded_int, _Atom):
    max = 1<<32
    min = 0
    packfmt = endian+'I'

    
class Int64(_bounded_int, _Atom):
    max = 1<<63
    min = -max
    packfmt = endian+'q'
    
        
class Int64u(_bounded_int, _Atom):
    max = 1<<64
    min = 0
    packfmt = endian+'Q'
    

class Float32(float, _Atom):
    packfmt = endian+'f'
    
    
class Float64(float, _Atom):
    packfmt = endian+'d'
    

class Enumeration(Int32, enum.Enum):
    pass


class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1
    
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE   


class _FixedBytes(_XdrClass, bytes):
    packfmt = endian + '{0:d}s'
    unpackfmt = endian + '{0:d}s{1:d}s'
    
    def __new__(cls, data):
        if len(data) != cls.size:
            raise ValueError('Incorrect data size')
        return super().__new__(cls, data)
    
    def pack(self):
        padding = (block_size - self.size % block_size) % block_size
        return _pack(self.packfmt.format(self.size + padding), self)
    
    @classmethod
    def parse(cls, source):
        padding = (block_size - cls.size % block_size) % block_size
        tup, source = _unpack(cls.unpackfmt.format(cls.size, padding), source)
        return cls(tup[0]), source


class _VarBytes(_XdrClass, bytes):
    packfmt = endian + 'I{0:d}s'
    unpackfmt = endian + '{0:d}s{1:d}s'
    
    def __new__(cls, data):
        if len(data) > cls.size:
            raise ValueError('Incorrect data size')
        return super().__new__(cls, data)
    
    def pack(self):
        padding = (block_size - len(self) % block_size) % block_size
        return _pack(self.packfmt.format(len(self) + padding), len(self), self)
    
    @classmethod
    def parse(cls, source):
        size, source = Int32u.parse(source)
        padding = (block_size - size % block_size) % block_size
        tup, source = _unpack(cls.unpackfmt.format(size, padding), source)
        return cls(tup[0]), source

        
class FixedOpaque(_FixedBytes):
    pass
    
class VarOpaque(_VarBytes):
    pass

class String(_VarBytes):
    pass


class FixedArray(_XdrClass, tuple):
    def __new__(cls, arg):
        a = tuple(arg)
        if len(a) != cls.size:
            raise ValueError('Invalid number of elements')
        return super().__new__(cls, (cls.element_type(x) for x in a))
    
    def pack(self):
        return b''.join(e.pack() for e in self)
    
    @classmethod
    def parse(cls, source):
        data = []
        for _ in range(cls.size):
            item, source = cls.element_type.parse(source)
            data.append(item)
        return cls(data), source
            

class VarArray(_XdrClass, tuple):
    def __new__(cls, arg):
        a = tuple(arg)
        if len(a) > cls.size:
            raise ValueError('Invalid number of elements')
        return super().__new__(cls, (cls.element_type(x) for x in a))
    
    def pack(self):
        return Int32u(len(self)).pack() + b''.join(e.pack() for e in self)
    
    @classmethod
    def parse(cls, source):
        size, source = Int32u.parse(source)
        data = []
        for _ in range(size):
            item, source = cls.element_type.parse(source)
            data.append(item)
        return cls(data), source
            
            