'''
Created on 12 sep. 2016

@author: Ruud
'''

import types
import sys
import inspect
from xdrlib2.parser import xdrSemantics

class XdrSyntaxError(SyntaxError):
    pass


class Semantics(xdrSemantics):
    def __init__(self):
        self.context = {}
        self.names = {}
        
#     def specification(self, ast):
#         name = 'example'
#         mod = types.ModuleType(name)
#         mod.__dict__.update(self.context)
#         sys.modules[name] = mod
#         
#         # Get global namespace where the 'use' function was called
#         # The enumerated values are added to this namespace
#         for f in inspect.stack():
#             if f.function == 'use':
#                 calling_frame = f.framee.f_back
#                 global_namespace = calling_frame.f_globals
#                 local_namespace = calling_frame.f_locals
#                 break
#         else:
#             # Outermost caller reached.
#             # Something is seriously wrong.
#             raise RuntimeError('Cannot determine calling global namespace')
#         
#         exec('import example', global_namespace, local_namespace)
        
    def specification(self, ast):
        # Import the whole stuff
        print(self.names)
        return ast

    def decimal_constant(self, ast):
        ast[0] = int(ast[0])
        return ast
    
    def hexadecimal_constant(self, ast):
        ast[0] = int(ast[0], 16)
        return ast
    
    def octal_constant(self, ast):
        ast[0] = int(ast[0], 7)
        return ast
    
    def constant_def(self, ast):
        name = ast['name']
        value = ast['value']
        if name in self.names:
            raise XdrSyntaxError("Name'{}' already defined".format(name))
        self.names[name] = value
        return ast
    
    
    
        
        
        
        