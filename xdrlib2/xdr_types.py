'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct

block_size = 4
endian = '>'  # Big-endian format character for struct.pack

class _bounded_int(int):
    def __new__(cls, value):
        if cls.min <= value < cls.max:
            return super().__new__(cls, value)
        raise ValueError()
    
    def pack(self):
        return struct.pack(self.packfmt, self) # + self.padding
    
    @classmethod
    def unpack(cls, source):
        tup = struct.unpack(cls.packfmt, source)
        return cls(tup[0])


class int32(_bounded_int):
    max = 1<<31
    min = -max
    packfmt = endian+'i'
    
        
class uint32(_bounded_int):
    max = 1<<32
    min = 0
    packfmt = endian+'I'

    
class int64(_bounded_int):
    max = 1<<63
    min = -max
    packfmt = endian+'q'
    
        
class uint64(_bounded_int):
    max = 1<<64
    min = 0
    packfmt = endian+'Q'
    

class float32(float):
    packfmt = endian+'f'
    
    def __new__(cls, v):
        return super().__new__(cls, v)
    
    def pack(self):
        return struct.pack(self.packfmt, self)
    
    @classmethod
    def unpack(cls, source):
        tup = struct.unpack(cls.packfmt, source)
        return cls(tup[0])

    
class float64(float):
    packfmt = endian+'d'
    
    def __new__(cls, v):
        return super().__new__(cls, v)
    
    def pack(self):
        return struct.pack(self.packfmt, self)
    
    @classmethod
    def unpack(cls, source):
        tup = struct.unpack(cls.packfmt, source)
        return cls(tup[0])
    
    