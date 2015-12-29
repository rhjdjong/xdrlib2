'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import enum

block_size = 4
endian = '>'  # Big-endian format character for struct.pack

class _bounded_int(int):
    def __new__(cls, value):
        if cls.min <= value < cls.max:
            return super().__new__(cls, value)
        raise ValueError()

class _packable:    
    def pack(self):
        return struct.pack(self.packfmt, self) # + self.padding
    
    @classmethod
    def unpack(cls, source):
        tup = struct.unpack(cls.packfmt, source)
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
    