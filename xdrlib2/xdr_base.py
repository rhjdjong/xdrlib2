'''
Created on 29 aug. 2016

@author: Ruud
'''

import configparser
import os
import re
from functools import singledispatch, update_wrapper

_install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

config_file = os.path.join(_install_dir, 'etc', 'xdr.ini')

config = configparser.ConfigParser()
with open(os.path.join(config_file)) as f:
    config.read_file(f)

if config['DEFAULT'].get('install_dir') != _install_dir:
    config['DEFAULT']['install_dir'] = _install_dir
    with open(config_file, "w") as f:
        config.write(f)

_xdr_settings = config['xdr']

block_size = _xdr_settings.getint('block_size', fallback=4)
'''The XDR basic block size defaults 4 bytes. All XDR data elements are encoded to a byte sequence with a length that is a multiple of the basic block size.
If necessary, the byte sequences are padded with NULL bytes.'''

endian = _xdr_settings.get('endian', '>')
'''Single character that indicates the byte order, as defined in the :mod:`struct` module. XDR defaults to big-endian byte order.''' 

byteorder = 'big' if endian == '>' else 'little'


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
    