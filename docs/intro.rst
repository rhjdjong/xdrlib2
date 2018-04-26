Introduction
============

The XDR standard :rfc:`4506` defines a serialization format for
several concrete data types.
The :mod:`xdrlib2` module provides a Python implementation of these data types
that free the user of worrying about the details of serialization
of complex data types.

The following example XDR specification is taken from :rfc:`4506`.

.. code-block:: C

   const MAXUSERNAME = 32;     /* max length of a user name */
   const MAXFILELEN = 65535;   /* max length of a file      */
   const MAXNAMELEN = 255;     /* max length of a file name */

   /*
    * Types of files:
    */
   enum filekind {
      TEXT = 0,       /* ascii data */
      DATA = 1,       /* raw data   */
      EXEC = 2        /* executable */
   };

   /*
    * File information, per kind of file:
    */
   union filetype switch (filekind kind) {
   case TEXT:
      void;                           /* no extra information */
   case DATA:
      string creator<MAXNAMELEN>;     /* data creator         */
   case EXEC:
      string interpretor<MAXNAMELEN>; /* program interpretor  */
   };

   /*
    * A complete file:
    */
   struct file {
      string filename<MAXNAMELEN>; /* name of file    */
      filetype type;               /* info about file */
      string owner<MAXUSERNAME>;   /* owner of file   */
      opaque data<MAXFILELEN>;     /* file data       */
   };

The Python equivalent of this specification is:

.. code-block:: python

   from xdrlib2 import Enumeration, Union, Void, String, Struct, VarOpaque

   MAXUSERNAME = 32    # max length of a user name
   MAXFILELEN = 65535  # max length of a file
   MAXNAMELEN = 255    # max length of a file name

   #
   # Types of files:
   #
   class filekind{Enumeration):
      TEXT = 0  # ascii data
      DATA = 1  # raw data
      EXEC = 2  # executable

   TEXT = filekind.TEXT
   DATA = filekind.DATA
   EXEC = filekind.EXEC

   #
   # File information, per kind of file:
   #
   with Union.typedef('filetype', kind=filekind) as filetype:
      filetype.case(TEXT, Void)
      filetype.case(DATA, creator=String.typedef('creator', size=MAXNAMELEN))
      filetype.case(EXEC, interpretor=String.typedef('interpretor', size=MAXNAMELEN))

   #
   # A complete file:
   #
   class file(Struct):
      filename = String.typedef('filename', size=MAXNAMELEN)  # name of file
      type = filetype                                         # info about file
      owner = String.typedef('owner', size='MAXUSERNAME')     # owner of file
      data = VarOpaque.typedef('data', size='MAXFILELEN')     # file data

Assuming that the above Python definitions are stored in a Python module :mod:`rfc_example`,
when we follow the example in :rfc:`4506`, with a user named 'John',
a lisp program 'sillyprog' that contains the data '(quit)',
the corresponding Python object would be created as:

.. code-block:: python

   >>> from rfc_example import file, filekind
   >>> myfile = file('sillyprog', (filekind.EXEC, 'lisp'), 'john', b'(quit)')

This object would be encoded by calling the `encode` function on this object:

.. code-block:: python

   >>> bindata = xdrlib2.encode(myfile)

And the object can be reconstructed by calling the `decode` function on the bytestring:

.. code-block:: python

   >>> myfile2 = xdrlib2.decode(file, bindata)
   >>> print(myfile2.filename)
   sillyprog
   >>> print(myfile2.type)
   {EXEC(2):lisp}
   >>> print(myfile2.type.interpretor)
   lisp
   >>> print(myfile2.owner)
   john
   >>> print(myfile2.data)
   b'(quit)'
