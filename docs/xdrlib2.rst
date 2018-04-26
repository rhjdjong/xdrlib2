.. Copyright (c) 2018 Ruud de Jong
   This file is part of the xdrlib2 project
   which is released under the MIT license.
   See https://github.com/rhjdjong/xdrlib2 for details.

===============
Module contents
===============

*********
Functions
*********

The :mod:`xdrlib2` module offers the following generic functions
that can be used on all XDR types:

.. autofunction:: xdrlib2.encode
.. autofunction:: xdrlib2.decode


*******
Classes
*******

.. autoclass:: xdrlib2.XdrType

Integer types
=============

.. autoclass:: xdrlib2.XdrInteger

The following concrete integer subclasses are provided:

.. class:: xdrlib2.Int32
.. class:: xdrlib2.Integer

   .. attribute:: min = -2147483648
   .. attribute:: max = 2147483648
   .. attribute:: signed = True
   .. attribute:: packed_size = 4

   These are concrete signed integer subclasses
   that have an encoding size of 4 bytes.
   They accept values
   between -2\ :sup:`31` (-2147483648) inclusive and
   2\ :sup:`31` (2147483648) exclusive.

   :class:`xdrlib2.Integer` is an alias of :class:`xdrlib2.Int32`


.. class:: xdrlib2.Int32u
.. class:: xdrlib2.UnsignedInteger

   .. attribute:: min = 0
   .. attribute:: max = 4294967296
   .. attribute:: signed = False
   .. attribute:: packed_size = 4

   These are concrete unsigned integer subclasses
   that have an encoding size of 4 bytes.
   They accept values
   between 0 inclusive and
   2\ :sup:`32` (4294967296) exclusive.

   :class:`xdrlib2.UnsignedInteger` is an alias of :class:`xdrlib2.Int32u`


.. class:: xdrlib2.Int64
.. class:: xdrlib2.Hyper

   .. attribute:: min = -9223372036854775808
   .. attribute:: max = 9223372036854775808
   .. attribute:: signed = True
   .. attribute:: packed_size = 8

   These are concrete signed integer subclasses
   that have an encoding size of 8 bytes.
   They accept values
   between -2\ :sup:`63` (-9223372036854775808) inclusive and
   2\ :sup:`63` (9223372036854775808) exclusive.

   :class:`xdrlib2.Hyper` is an alias of :class:`xdrlib2.Int64`


.. class:: xdrlib2.Int64u
.. class:: xdrlib2.UnsignedHyper

   .. attribute:: min = 0
   .. attribute:: max = 18446744073709551616
   .. attribute:: signed = False
   .. attribute:: packed_size = 8

   These are concrete unsigned integer subclasses
   that have an encoding size of 8 bytes.
   They accept values
   between 0 inclusive and
   2\ :sup:`64` (18446744073709551616) exclusive.

   :class:`xdrlib2.UnsignedHyper` is an alias of :class:`xdrlib2.Int64u`


Additional concrete integer subclasses can be created by subclassing :class:`XdrInteger`
with appropriate parameters `min` and `max`, subject to the restriction that
`min` ≤ 0 < `max`.
The values allowed for the subclass are between `min` (inclusive)
and `max` (exclusive).
As an example, the following will define an 8-bit unsigned integer type
and a 16-bit signed integer type:

.. code-block:: python

   Int8u = XdrInteger.typedef('Int8u', min=0, max=1<<8)
   Int16 = XdrInteger.typedef('Int16', min=-1<<15, max=1<<15)


Original :mod:`xdrlib` module
=============================

As a convenience to users of the :mod:`xdrlib` module from the standard library,
module :mod:`xdrlib2` makes the contents of :mod:`xdrlib` available.
This is merely an aid to transition to the higher-level constructs offered
by :mod:`xdrlib2` -- no development will be done to enhance the :class:`Packer`
and :class:`Unpacker` classes in :mod:`xdrlib` to support the more complex
data structure that :mod:`xdrlib2` can handle.

