# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from . import xdr_core

Integer = xdr_core.Int32
UnsignedInteger = xdr_core.Int32u
Hyper = xdr_core.Int64
UnsignedHyper = xdr_core.Int64u
Float = xdr_core.Float32
Double = xdr_core.Float64
Quadruple = xdr_core.Float128

Enumeration = xdr_core.XDR_Enumeration


class Boolean(Enumeration, FALSE=0, TRUE=1):
    pass
