'''
Created on 29 aug. 2016

@author: Ruud
'''
import re
from functools import singledispatch, update_wrapper

block_size = 4
'''The XDR basic block size is 4 bytes. All XDR data elements are encoded to a byte sequence with a length that is a multiple of the basic block size.
If necessary, the byte sequences are padded with NULL bytes.'''

endian = '>'  # Big-endian format character for struct.pack
'''Single character that indicates the byte order, as defined in the :mod:`struct` module. XDR uses big-endian byte order.''' 

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

_name_re = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')

def _is_valid_name(name):
    if name.startswith('*'):
        name = name[1:]
    return True if _name_re.match(name) and not name in _reserved_words else False

def _methoddispatch(func):
    dispatcher = singledispatch(func)
    def wrapper(*args, **kwargs):
        return dispatcher.dispatch(args[1].__class__)(*args, **kwargs)
    wrapper.register = dispatcher.register
    update_wrapper(wrapper, dispatcher)
    return wrapper
    