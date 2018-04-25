.. Copyright (c) 2018 Ruud de Jong
   This file is part of the xdrlib2 project which is released under the MIT license.
   See https://github.com/rhjdjong/xdrlib2 for details.

===============
Module contents
===============

XDR Types
=========

General
-------

All type classes in :mod:`xdrlib2`, as well as user-defined classes derived from these,
offer the following methods:

.. method:: encode

   `xdrobj.encode()` returns the byte representation of the XDR encoding of the
   value of `xdrobj`.

.. classmethod:: decode

   `xdrcls.decode(bytestring)` returns an instantiation of class :class:`xdrcls`
   with the value as encoded in the `bytestring` argument.
   It raises a :exc:`ValueError` if the bytes in `bytestring`
   do not represent a valid value for the class :class:`xdrcls`.

Numeric types
-------------

The following numeric types can be instantiated with an Optional
integer argument. Their default value when instantiated is 0.

.. class:: Int32(v=0)

   This is the implementation of the `int` type in the XDR specification.

.. class:: Int32u(v=0)

   This is the implementation of the `unsigned int` type in the XDR specifcation.

.. class:: Int64(v=0)

   This is the implementation of the `hyper` type in the XDR specifcation.

.. class:: Int64u(v=0)

   This is the implementation of the `unsigned hyper` type in the XDR specification.



Original :mod:`xdrlib` module
=============================

As a convenience to users of the :mod:`xdrlib` module from the standard library,
module :mod:`xdrlib2` makes the contents of :mod:`xdrlib` available.
This is merely an aid to transition to the higher-level constructs offered
by :mod:`xdrlib2` -- no development will be done to enhance the :class:`Packer`
and :class:`Unpacker` classes in :mod:`xdrlib` to support the more complex
data structure that :mod:`xdrlib2` can handle.

