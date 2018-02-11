# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from . import xdr_core

class Int32(xdr_core._XDR_integer, size=32, signed=True): pass


class Int32u(xdr_core._XDR_integer, size=32, signed=False): pass


class Int64(xdr_core._XDR_integer, size=64, signed=True): pass


class Int64u(xdr_core._XDR_integer, size=64, signed=False): pass



class Float32(xdr_core._XDR_float, exponent_size=8, fraction_size=23): pass


class Float64(xdr_core._XDR_float, exponent_size=11, fraction_size=52): pass


class Float128(xdr_core._XDR_float, exponent_size=15, fraction_size=112): pass

