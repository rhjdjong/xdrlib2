.. image:: https://readthedocs.org/projects/xdrlib2/badge/?version=latest
   :target: http://xdrlib2.readthedocs.org/en/latest/?badge=latest
   :alt: ReadTheDocs Documentation Status

.. image:: https://travis-ci.org/rhjdjong/xdrlib2.svg
   :target: https://travis-ci.org/rhjdjong/xdrlib2
   :alt: Travis Test Status

.. image:: https://ci.appveyor.com/api/projects/status/7585iqu3kv7hru3s?svg=true
   :target: https://ci.appveyor.com/project/RuuddeJong/xdrlib2
   :alt: AppVeyor Test Status



=============================================
``xdrlib2`` --- A module for the XDR standard
=============================================


The `xdrlib2` module is a drop-in replacmeent for the `xdrlib` package
in Python's standard libarary.
The differences with the `xdrlib` package are:

 - `xdrlib2` implements :rfc:`4506`, which obsoletes :rfc:`1832`, which in turn replaced :rfc:`1014`.
   The standard library's `xdrlib` package on the other hand only partially implements
   the obsolete :rfc:`1014`.
 - `xdrlib2` can interpret files with XDR specifications, and translate
   these into Python modules with the appropriate types. This allows
   users of the `xdrlib2` to directly use the high-level XDR data structures
   defined in the specifications. That is not possible with `xdrlib`, because
   deals only with basic integer, float, and list types.
