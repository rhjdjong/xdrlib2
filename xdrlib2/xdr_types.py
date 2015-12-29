'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import enum

block_size = 4
endian = '>'  # Big-endian format character for struct.pack


def _pack(fmt, *vars):
    try:
        return struct.pack(fmt, *vars)
    except struct.error as e:
        raise ValueError("Packing error") from e

def _unpack(fmt, source):
    try:
        return struct.unpack(fmt, source)
    except struct.error as e:
        raise ValueError("Unpacking error") from e

    
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
        tup = _unpack(cls.packfmt, source)
        return cls(tup[0])


class Int32(_bounded_int, _packable):
    max = 1<<31
    min = -max
    packfmt = endian+'i'
    
        
class Int32u(_bounded_int, _packable):
    max = 1<<32
    min = 0
    packfmt = endian+'I'

    
class Int64(_bounded_int, _packable):
    max = 1<<63
    min = -max
    packfmt = endian+'q'
    
        
class Int64u(_bounded_int, _packable):
    max = 1<<64
    min = 0
    packfmt = endian+'Q'
    

class Float32(float, _packable):
    packfmt = endian+'f'
    
    
class Float64(float, _packable):
    packfmt = endian+'d'
    

class Enumeration(Int32, enum.Enum):
    pass


class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1
    
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE   


class FixedOpaque(bytes):
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
    def unpack(cls, source):
        padding = (block_size - cls.size % block_size) % block_size
        tup = _unpack(cls.unpackfmt.format(cls.size, padding), source)
        return cls(tup[0])
    
class VarOpaque(bytes):
    packfmt = endian + 'I{0:d}s'
    unpackfmt = endian + 'I{0:d}s{1:d}s'
    
    def __new__(cls, data):
        if len(data) > cls.size:
            raise ValueError('Incorrect data size')
        return super().__new__(cls, data)
    
    def pack(self):
        packsize = block_size * (len(self) // block_size + 1)
        return struct.pack(self.packfmt.format(packsize), len(self), self)
    
    @classmethod
    def unpack(cls, source):
        size = Int32u.unpack(source[:4])
        padding = (block_size - size % block_size) % block_size
        tup = _unpack(cls.unpackfmt.format(size, padding), source)
        return cls(tup[1])
        
        