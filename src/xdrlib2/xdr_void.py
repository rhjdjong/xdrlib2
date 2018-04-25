# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType, xdr_mode
from .xdr_enumeration import FALSE

class Void(XdrType):
    _mode = xdr_mode.FINAL
    # _final = True
    # _abstract = False

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._mode is xdr_mode.FINAL:
            if parameters:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")

    def __new__(cls, _=None):
        # Ignore any other base classes
        return super(XdrType, cls).__new__(cls)

    def __init__(self, _=None):
        # Ignore any other base classes
        super(XdrType, self).__init__()

    # @classmethod
    # def _validate_arguments(cls):
    #     pass

    def _encode_(self):
        if self._optional:
            return FALSE._encode_()
        else:
            return b''

    @classmethod
    def _decode_(cls, bstr):
        return cls(None), bstr

    def __eq__(self, other):
        return other is None or isinstance(other, Void)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'Void()'

    def __str__(self):
        return 'None'
