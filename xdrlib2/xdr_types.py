'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import enum

from functools import singledispatch, update_wrapper
from collections import OrderedDict

_reserved_words = {'bool',
                   'case',
                   'const',
                   'default',
                   'double',
                   'quadruple',
                   'enum',
                   'float',
                   'hyper',
                   'int',
                   'opaque',
                   'string',
                   'struct',
                   'switch',
                   'typedef',
                   'union',
                   'unsigned',
                   'void',
                   }


def _methoddispatch(func):
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
    
    def __repr__(self):
        return ':'.join((self.__class__.__name__, super().__repr__()))
    
    def __eq__(self, other):
        return super().__eq__(other)
    
    @classmethod
    def make_type(cls, name, *args, **kwargs):
        if name in _reserved_words:
            raise ValueError('Invalid name for derived class: {}'.format(name))
        return cls.__class__(name, (cls,), cls._make_class_dictionary(*args, **kwargs))
    
    @classmethod
    def _make_class_dictionary(cls, *args, **kwargs):
        raise NotImplementedError

class _Atomic(_XdrClass):
    def _pack(self):
        return _pack(self._packfmt, self)
    
    @classmethod
    def _parse(cls, source):
        tup, source = _unpack(cls._packfmt, source)
        return cls(tup[0]), source
    
    @classmethod
    def _make_class_dictionary(cls, *args, **kwargs):
        return {}
    
    
class _Integer(_Atomic):
    def __new__(cls, value):
        if cls._min <= value < cls._max:
            return super().__new__(cls, value)
        raise ValueError('Value out of range')
    

class Int32(_bounded_int, _Integer):
    _max = 1<<31
    _min = -_max
    _packfmt = endian+'i'
    
Int32Type = Int32.make_type   
        
class Int32u(_bounded_int, _Integer):
    _max = 1<<32
    _min = 0
    _packfmt = endian+'I'

Int32uType = Int32u.make_type
    
class Int64(_bounded_int, _Integer):
    _max = 1<<63
    _min = -_max
    _packfmt = endian+'q'
    
Int64Type = Int64.make_type

        
class Int64u(_bounded_int, _Integer):
    _max = 1<<64
    _min = 0
    _packfmt = endian+'Q'
    
Int64uType = Int64u.make_type


class Float32(float, _Atomic):
    _packfmt = endian+'f'
    
Float32Type = Float32.make_type

    
class Float64(float, _Integer):
    _packfmt = endian+'d'

Float64Type = Float64.make_type
    

class Enumeration(Int32, enum.Enum):
    @classmethod
    def _make_class_dictionary(cls, **kwargs):
        return kwargs
    
    @classmethod
    def make_type(cls, name, **kwargs):
        return cls(name, kwargs)

EnumerationType = Enumeration.make_type


class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1
    
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE   


class _Bytes(_XdrClass, bytearray):
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
    
    @classmethod
    def _make_class_dictionary(cls, size):
        return {'_size': size}
    
    
class FixedOpaque(_Bytes):
    _fixed = True

FixedOpaqueType = FixedOpaque.make_type

  
class VarOpaque(_Bytes):
    _fixed = False

VarOpaqueType = VarOpaque.make_type

  
class String(_Bytes):
    _fixed = False

StringType = String.make_type
  

class _Array(_XdrClass, list):
    
    def __init__(self, arg):
        a = tuple(arg)
        data_size = len(a)
        if data_size > self._size or self._fixed and data_size < self._size:
            raise ValueError('Incorrect number of elements')
        super().__init__(self._element_type(x) for x in a)
    
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
            
    @classmethod
    def _make_class_dictionary(cls, size, element_type):
        return {'_size': size, '_element_type': element_type}
            

class FixedArray(_Array):
    _fixed = True

FixedArrayType = FixedArray.make_type


class VarArray(_Array):
    _fixed = False

VarArrayType = VarArray.make_type


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

        
class Structure(_XdrClass, OrderedDict, metaclass=_StructureMeta):
    def __init__(self, **kwargs):
        sentinel = object()
        for name in self._members:
            self[name] = sentinel

        for name, value in kwargs.items():
            try:
                component_type = self._members[name]
            except KeyError:
                raise ValueError('Unknown structure component: {}'.format(name))
            self[name] = component_type(value)
            
        if sentinel in self.values():
                raise ValueError('Missing initialization for component {}'.format(name))

    def __getattr__(self, name):
        if name in self:
            return self[name]
        return super().__getattr__(name)  
    
    @_methoddispatch
    def __eq__(self, other):
        return super().__eq__(other)
    
    @__eq__.register(_XdrClass)
    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return super().__eq__(other)
    
    def _pack(self):
        return b''.join(self[n]._pack() for n in self)
    
    @classmethod
    def _parse(cls, source):
        result = {}
        for name, typ in cls._members.items():
            obj, source = typ._parse(source)
            result[name] = obj
        return cls(**result), source
    
    @classmethod
    def _make_class_dictionary(cls, *args):
        return OrderedDict(args)
            

StructureType = Structure.make_type


class Void(_XdrClass):
    _instance = None
    
    def __new__(cls, _=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _pack(self):
        return b''

    def __eq__(self, other):
        return (other is None or isinstance(other, Void))
                
    @classmethod
    def _parse(cls, source):
        return cls(), source
     

class _UnionMeta(type):
    def __new__(cls, name, bases, dct):
        if not ('discriminant' in dct and 'variants' in dct):
            return super().__new__(cls, name, bases, dct)
        
        discr = dct['discriminant']
        if isinstance(discr, type):
            d_name, d_type = discr.__name__, discr
        else:
            d_name, d_type = discr
            
        v_info = dct['variants']
        
        if not isinstance(d_name, str) or d_name in _reserved_words:
            raise ValueError("Invalid union discriminant name: {}".format(d_name))
        if not isinstance(d_type, type):
            raise ValueError("Discriminant type must be a class")
        if not issubclass(d_type, (Int32, Int32u, Enumeration)):
            raise ValueError("Invalid type for union discriminant: {}".format(d_type))
        if not isinstance(v_info, dict):
            raise ValueError("Union variants must be specified as mapping "
                            "(discriminant value) -> (variant_name, variant_type)")
            
        variants = {}
        variants_by_name = {}
        
        for d_value, v_arm_info in v_info.items():
            if d_value != 'default':
                d_value = d_type(d_value)
                
            if v_arm_info is None:
                v_name = ''
                v_type = Void
            elif isinstance(v_arm_info, type) and issubclass(v_arm_info, _XdrClass):
                v_name, v_type = v_arm_info.__name__, v_arm_info
            else:
                v_name, v_type = v_arm_info
                if v_type is None:
                    v_type = Void
            if not isinstance(v_name, str) or v_name in _reserved_words:
                raise ValueError("Invalid name for union variant {}: {}".format(d_value, v_name))
            if not issubclass(v_type, _XdrClass):
                raise ValueError("Invalid type for union variant {}: {}".format(d_value, v_type))
            variants[d_value] = (v_name, v_type)
            variants_by_name[v_name] = (d_value, v_type)
        
        del dct['discriminant']
        del dct['variants']
        dct['_d_name'] = d_name
        dct['_d_type'] = d_type
        dct['_variants'] = variants
        dct['_variants_by_name'] = variants_by_name
    
        return super().__new__(cls, name, bases, dct)

    @classmethod
    def __prepare__(mcls, cls, bases):
        return OrderedDict()

            
class Union(_XdrClass, OrderedDict, metaclass=_UnionMeta):
    def __new__(cls, *args, **kwargs):
        try:
            cls._d_name
            cls._d_type
            cls._variants
            cls._variants_by_name
        except AttributeError:
            raise NotImplementedError('Use a Union subclass with discriminant and variants specified')
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        if len(kwargs) == 0 and len(args) == 0:
            raise ValueError('Union initialization requires discriminant and variant values')
        if len(kwargs) == 0:
            d = args[0]
            v = args[1:]
            if isinstance(d, str):
                if d == 'default':
                    d_value = d
                    try:
                        v_name, v_type = self._variants[d_value]
                    except KeyError:
                        raise ValueError('Union does not have a default variant')
                else:
                    v_name = d
                    try:
                        d_value, v_type = self._variants_by_name[v_name]
                    except KeyError:
                        raise ValueError('Invalid union variant name: {}'.format(v_name))
            else:
                d_value = self._d_type(d)
                if d_value in self._variants:
                    v_name, v_type = self._variants[d_value]
                elif 'default' in self._variants:
                    v_name, v_type = self._variants['default']
                else:
                    raise ValueError('Invalid union discriminant value: {}'.format(d_value))
        elif len(kwargs) == 1:
            v_name, *v = list(kwargs.items())[0]
            try:
                d_value, v_type = self._variants_by_name[v_name]
            except KeyError:
                raise ValueError('Invalid union variant name: {}'.format(v_name))
        else:
            raise ValueError('Invalid union initialization')
        
        self._d_value = d_value
        self._name = v_name
        self._value = v_type(*v)        
                
     
    @classmethod
    def _get_data_by_id(cls, id):
        try:
            return cls._variants[id]
        except KeyError:
            if 'default' in cls._variants:
                return cls._variants['default']
            else:
                raise ValueError('Invalid discriminant value: {}'.format(id))
     
    def __getattr__(self, name):
        if name == self._name:
            return self._value
        if name == self._d_name:
            return self._d_value
        if name == 'default' and self._d_value not in self._variants:
            return self._value
        raise AttributeError('Invalid variant name')
     
    def __getitem__(self, index):
        if index == self._d_value:
            return self._value
        raise KeyError('Invalid variant index')
     
#     def __eq__(self, other):
#         if self.__class__ != other.__class__:
#             return False
#         return (self._discriminant == other._discriminant and
#                 self._value == other._value and
#                 self._name == other._name)
#     
    def _pack(self):
        return self._d_value._pack() + self._value._pack()
     
    @classmethod
    def _parse(cls, source):
        discriminant, source = cls._d_type._parse(source)
        _, v_type = cls._get_data_by_id(discriminant)
        variant, source = v_type._parse(source)
        return cls(discriminant, variant), source

    @classmethod
    def _make_class_dictionary(cls, **kwargs):
        return kwargs
 
UnionType = Union.make_type

def Optional(cls):
    opt_cls = UnionType('*'+cls.__name__,
                         discriminant=('opted', Boolean),
                         variants={FALSE: None, TRUE: ('element', cls)})
    opt_cls._original_new = opt_cls.__new__
    def opt_new(cls, *args, **kwargs):
        if len(args) + len(kwargs) == 0:
            return cls._original_new(FALSE)
        elif len(kwargs) == 0 and len(args) == 1 and args[0] is None:
            return cls._original_new(FALSE)
        else:
            return cls._original_new(TRUE, *args, **kwargs)
    opt_cls.__new__ = opt_new
    return opt_cls

# def Optional(cls):
#     opt_cls = UnionType('*'+cls.__name__, ('opted', Boolean), {FALSE: None, TRUE: ('element', cls)})
#     opt_cls._original_new = opt_cls.__new__
#     def opt_new(cls, *args, **kwargs):
#         if len(args) + len(kwargs) == 0 or (len(args)>0 and args[0] is None):
#             return cls._original_new(False)
#         return cls._original_new(True, *args, **kwargs)
#     opt_cls.__new__ = opt_new
#     return opt_cls
    
            
        