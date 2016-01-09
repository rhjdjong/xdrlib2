'''
Created on 28 dec. 2015

@author: Ruud de Jong
'''

import struct
import re

from functools import singledispatch, update_wrapper
from collections import OrderedDict

reserved_words = {'bool',
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

_name_re = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
def is_valid_name(name):
    return True if _name_re.match(name) and not name in reserved_words else False

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

    def __add__(self, other):
        return self.__class__(super().__add__(other))
    
    def __sub__(self, other):
        return self.__class__(super().__sub__(other))
    
    def __mul__(self, other):
        return self.__class__(super().__mul__(other))
    
    def __matmul__(self, other):
        return self.__class__(super().__matmul__(other))
    
    def __truediv__(self, other):
        return self.__class__(super().__truediv__(other))
    
    def __floordiv__(self, other):
        return self.__class__(super().__floordiv__(other))
    
    def __mod__(self, other):
        return self.__class__(super().__mod__(other))
    
    def __pow__(self, *args):
        return self.__class__(super().__pow__(*args))

    def __lshift__(self, other):
        return self.__class__(super().__lshift__(other))
    
    def __rshift__(self, other):
        return self.__class__(super().__rshift__(other))
    
    def __and__(self, other):
        return self.__class__(super().__and__(other))
    
    def __xor__(self, other):
        return self.__class__(super().__xor__(other))
    
    def __or__(self, other):
        return self.__class__(super().__or__(other))
    
    def __radd__(self, other):
        return self.__class__(super().__radd__(other))
    
    def __rsub__(self, other):
        return self.__class__(super().__rsub__(other))
    
    def __rmul__(self, other):
        return self.__class__(super().__rmul__(other))
    
    def __rmatmul__(self, other):
        return self.__class__(super().__rmatmul__(other))
    
    def __rtruediv__(self, other):
        return self.__class__(super().__rtruediv__(other))
    
    def __rfloordiv__(self, other):
        return self.__class__(super().__rfloordiv__(other))
    
    def __rmod__(self, other):
        return self.__class__(super().__rmod__(other))
    
    def __rpow__(self, *args):
        return self.__class__(super().__rpow__(*args))

    def __rlshift__(self, other):
        return self.__class__(super().__rlshift__(other))
    
    def __rrshift__(self, other):
        return self.__class__(super().__rrshift__(other))
    
    def __rand__(self, other):
        return self.__class__(super().__rand__(other))
    
    def __rxor__(self, other):
        return self.__class__(super().__rxor__(other))
    
    def __ror__(self, other):
        return self.__class__(super().__ror__(other))
    
    def __iadd__(self, other):
        return self.__class__(super().__iadd__(other))
    
    def __isub__(self, other):
        return self.__class__(super().__isub__(other))
    
    def __imul__(self, other):
        return self.__class__(super().__imul__(other))
    
    def __imatmul__(self, other):
        return self.__class__(super().__imatmul__(other))
    
    def __itruediv__(self, other):
        return self.__class__(super().__itruediv__(other))
    
    def __ifloordiv__(self, other):
        return self.__class__(super().__ifloordiv__(other))
    
    def __imod__(self, other):
        return self.__class__(super().__imod__(other))
    
    def __ipow__(self, *args):
        return self.__class__(super().__ipow__(*args))

    def __ilshift__(self, other):
        return self.__class__(super().__ilshift__(other))
    
    def __irshift__(self, other):
        return self.__class__(super().__irshift__(other))
    
    def __iand__(self, other):
        return self.__class__(super().__iand__(other))
    
    def __ixor__(self, other):
        return self.__class__(super().__ixor__(other))
    
    def __ior__(self, other):
        return self.__class__(super().__ior__(other))
    
    def __neg__(self):
        return self.__class__(super().__neg__())
    
    def __pos__(self):
        return self.__class__(super().__pos__())
    
    def __abs__(self):
        return self.__class__(super().__abs__())
    
    def __invert__(self):
        return self.__class__(super().__invert__())
    

    @classmethod
    def make_type(cls, name, *args, **kwargs):
        if not isinstance(name, str) or name and not is_valid_name(name):
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
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        
    def __index__(self):
        return int(self)
    
    def __invert__(self):
        return self.__class__(self._max - self._min - 1 - self)
        

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
    
class _EnumerationMeta(type):
    def __new__(cls, name, bases, dct):
        members = {}
        for n, v in dct.items():
            if not is_valid_name(n): continue
            if callable(v): continue
            if isinstance(v, (classmethod, staticmethod)): continue
            try:
                members[n] = Int32(v)
            except (ValueError, TypeError):
                raise ValueError('Invalid enumeration value for name {}: {}'.format(n, v))
        for n in members:
            del dct[n]    
        dct['_members'] = members
        dct['_values'] = set(members.values())
        return super().__new__(cls, name, bases, dct)
    
    def __getattr__(self, name):
        try:
            return self._members[name]
        except KeyError:
            raise ValueError('Invalid name for enumeration class {}: {}'.format(self.__name__, name))
    
    
class Enumeration(Int32, metaclass=_EnumerationMeta):
    def __new__(cls, value):
        v = super().__new__(cls, value)
        if v in cls._members.values():
            return v
        raise ValueError('Invalid enumeration value for class {}: {}'.format(cls.__name__, value))
    
    @classmethod
    def _make_class_dictionary(cls, **kwargs):
        return kwargs
    
EnumerationType = Enumeration.make_type


class Boolean(Enumeration):
    FALSE = 0
    TRUE = 1
    
FALSE = Boolean.FALSE
TRUE = Boolean.TRUE   

class _Seq(_XdrClass):
    def __new__(cls, data):
        t = tuple(iter(data))
        cls.check_size(len(t))
        return super().__new__(cls, t)
    
    @_methoddispatch   
    def __delitem__(self, index):
        self.check_size(len(self) - 1)
        super().__delitem__(index)
    
    @__delitem__.register(slice)
    def _delslice(self, sl):
        self.check_size(len(self) - len(self[sl]))
        super().__delitem__(sl)

    
class _Bytes(_Seq, bytearray):
    _packfmt = endian + '{0:d}s'
    _unpackfmt = endian + '{0:d}s{1:d}s'

#     def __new__(cls, data):
#         t = bytes(data)
#         cls.check_size(len(t))
#         return super().__new__(cls, t)
#     
    
    @classmethod
    def _make_class_dictionary(cls, size):
        return {'_size': size}

    def append(self, value):
        self.check_size(len(self)+1)
        super().append(value)
    
    def extend(self, it):
        b = bytes(iter(it))
        self.check_size(len(self)+len(b))
        super().extend(b)
    
    @_methoddispatch
    def __setitem__(self, index, value):
        super().__setitem__(index, value)
    
    @__setitem__.register(slice)
    def _setslice(self, sl, value):
        value = bytes(iter(value))
        self.check_size(len(self) - len(self[sl]) + len(value))
        super().__setitem__(sl, value)
    
    

class _FixedBytes(_Bytes):
    @classmethod
    def check_size(cls, value):
        if value != cls._size:
            raise ValueError("Incorrect size: {}. Expected: {}".format(value, cls._size))
    
    def _pack(self):
        size = len(self)
        padded_size = ((size+block_size-1)//block_size)*block_size
        return _pack(self._packfmt.format(padded_size), self)
    
    @classmethod
    def _parse(cls, source):
        padding = (block_size - cls._size % block_size) % block_size
        tup, source = _unpack(cls._unpackfmt.format(cls._size, padding), source)
        return cls(tup[0]), source

    
class _VariableBytes(_Bytes):
    @classmethod
    def check_size(cls, value):
        if value > cls._size:
            raise ValueError("Size too large: {}. Maximum is {}". format(value, cls._size))

    def _pack(self):
        size = len(self)
        padded_size = ((size+block_size-1)//block_size)*block_size
        return Int32u(size)._pack() + _pack(self._packfmt.format(padded_size), self)

    @classmethod
    def _parse(cls, source):
        size, source = Int32u._parse(source)
        padding = (block_size - size % block_size) % block_size
        tup, source = _unpack(cls._unpackfmt.format(size, padding), source)
        return cls(tup[0]), source


class FixedOpaque(_FixedBytes):
    pass

FixedOpaqueType = FixedOpaque.make_type

  
class VarOpaque(_VariableBytes):
    pass

VarOpaqueType = VarOpaque.make_type

  
class String(_VariableBytes):
    pass

StringType = String.make_type
  

class _Array(_Seq, list):
    def __init__(self, arg):
        super().__init__(self._element_type(x) for x in iter(arg))
    
    @classmethod
    def _make_class_dictionary(cls, size, element_type):
        return {'_size': size, '_element_type': element_type}
    
    def append(self, value):
        self.check_size(len(self)+1)
        super().append(self._element_type(value))
    
    def extend(self, it):
        it = list(it)
        self.check_size(len(self)+len(it))
        super().extend(self._element_type(x) for x in it)
    
    @_methoddispatch
    def __setitem__(self, index, value):
        super().__setitem__(index, self._element_type(value))
    
    @__setitem__.register(slice)
    def _setslice(self, sl, value):
        value = list(value)
        self.check_size(len(self) - len(self[sl]) + len(value))
        super().__setitem__(sl, (self._element_type(v) for v in value))
    
        
class FixedArray(_Array):
    @classmethod
    def check_size(cls, value):
        if value != cls._size:
            raise ValueError("Incorrect size: {}. Expected: {}".format(value, cls._size))

    def _pack(self):
        return b''.join(e._pack() for e in self)
    
    @classmethod
    def _parse(cls, source):
        data = []
        for _ in range(cls._size):
            item, source = cls._element_type._parse(source)
            data.append(item)
        return cls(data), source
            
FixedArrayType = FixedArray.make_type


class VarArray(_Array):
    @classmethod
    def check_size(cls, value):
        if value > cls._size:
            raise ValueError("Size too large: {}. Maximum is {}". format(value, cls._size))

    def _pack(self):
        return Int32u(len(self))._pack() + b''.join(e._pack() for e in self)
    
    @classmethod
    def _parse(cls, source):
        size, source = Int32u._parse(source)
        data = []
        for _ in range(size):
            item, source = cls._element_type._parse(source)
            data.append(item)
        return cls(data), source
            
VarArrayType = VarArray.make_type


class _StructureMeta(type):
    def __new__(cls, name, bases, dct):
        members = OrderedDict()
        for n, v in dct.items():
            if not is_valid_name(n): continue
            members[n] = v
        for n in members:
            del dct[n]
        dct['_members'] = members
        return super().__new__(cls, name, bases, dct)
    
    @classmethod
    def __prepare__(mcls, cls, bases):
        return OrderedDict()

        
class Structure(_XdrClass, OrderedDict, metaclass=_StructureMeta):
    def __init__(self, *args, **kwargs):
        sentinel = object()
        for name in self._members:
            self[name] = sentinel
        
        for (name, component_type), value in zip(self._members.items(), args):
            self[name] = component_type(value)
        
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
    
    def __setattr__(self, name, value):
        if name in self:
            self[name] = self._members[name](value)
        else:
            super().__setattr__(name, value)
    
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
    
    def __init__(self, _=None):
        super().__init__()
        
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
        
        if not isinstance(d_name, str) or d_name and not is_valid_name(d_name):
            raise ValueError("Invalid union discriminant name: {}".format(d_name))
        if not isinstance(d_type, type):
            raise ValueError("Discriminant type must be a class")
        if not issubclass(d_type, (Int32, Int32u, Enumeration)):
            raise ValueError("Invalid type for union discriminant: {}".format(d_type))
        if not isinstance(v_info, dict):
            raise ValueError("Union variants must be specified as mapping "
                            "(discriminant value) -> (variant_name, variant_type)")
        
        def make_variant_type(v_name, v_type):
            class var_class(v_type):
                def __new__(cls, variant, *args, **kwargs):
                    obj = super().__new__(cls, *args, **kwargs)
                    obj.discr = d_type(variant)
                    obj.name = v_name
                    return obj
                
                def __init__(self, variant, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    
                def _pack(self):
                    return self.discr._pack() + super()._pack()
                
                @classmethod
                def _parse(cls, source):
                    v_value, source = v_type._parse(source)
                    return v_value, source
            return var_class
                        
                
        variant_type = {}
        variant_name = {}
        
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
            if not isinstance(v_name, str) or v_name and not is_valid_name(v_name):
                raise ValueError("Invalid name for union variant {}: {}".format(d_value, v_name))
            if not issubclass(v_type, _XdrClass):
                raise ValueError("Invalid type for union variant {}: {}".format(d_value, v_type))
            variant_type[d_value] = make_variant_type(v_name, v_type)
            variant_name[d_value] = v_name
        
        del dct['discriminant']
        del dct['variants']
        dct['_d_name'] = d_name
        dct['_d_type'] = d_type
        dct['_variant_type'] = variant_type
        dct['_variant_name'] = variant_name
    
        return super().__new__(cls, name, bases, dct)

    @classmethod
    def __prepare__(mcls, cls, bases):
        return OrderedDict()

            
class Union(_XdrClass, OrderedDict, metaclass=_UnionMeta):
    def __new__(cls, variant, *args, **kwargs):
        try:
            cls._d_name
            cls._d_type
            cls._variant_type
            cls._variant_name
        except AttributeError:
            raise NotImplementedError('Use a Union subclass with discriminant and variants specified')
        
        return cls._get_variant_type(variant)(variant, *args, **kwargs)
#         if variant in cls._variant_type:
#             return cls._variant_type[variant](variant, *args, **kwargs)
#         elif "default" in cls._variant_type:
#             return cls._variant_type["default"](variant, *args, **kwargs)
#         else:
#             raise ValueError('Invalid union variant: {}'.format(variant))

    @classmethod
    def _get_variant_type(cls, discr):
        try:
            return cls._variant_type[discr]
        except KeyError:
            if 'default' in cls._variant_type:
                return cls._variant_type['default']
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
     
    @classmethod
    def _parse(cls, source):
        discriminant, source = cls._d_type._parse(source)
        v_type = cls._get_variant_type(discriminant)
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
    
            
        