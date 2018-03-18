# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import inspect

from .xdr_core import XdrType, Void
from .xdr_enumeration import Boolean, FALSE, TRUE

class Optional(XdrType):
    """
    Optional(cls) --> optional class.

    The class Optional is primarily used as a decorator to create an optional XDR type.
    >>> from xdr_types import Optional, Integer, Void
    >>> opt_cls = Optional(Integer)
    >>>

    The name of the optional class is the name of the original class,
    prepended with an asterix '*'
    >>> opt_cls.__name__
    '*Int32'

    Class Optional is also a mix-in class for these optional XDR types.
    >>> issubclass(opt_cls, Optional)
    True

    An optional type in itself is not a subclass of the original type though.
    >>> issubclass(opt_cls, Integer)
    False

    The reason for that is that the actual type depends on whether or not
    the value with the optional type is present or not.

    When the value is present, it is an instance
    of both the original type and the optional type.
    >>> x = opt_cls(3)
    >>> isinstance(x, Integer)
    True
    >>> isinstance(x, opt_cls)
    True
    >>> isinstance(x, Optional)
    True

    When the value is absent, it is not an instance of the original type.
    Instead it is an instance of both Void and the optional type.
    >>> y = opt_cls(None)
    >>> isinstance(y, Integer)
    False
    >>> isinstance(y, Void)
    True
    >>> isinstance(y, opt_cls)
    True
    >>> isinstance(y, Optional)
    True

    Note that the actual types for present and absent values are different
    from each other, and different from the optional type
    >>> type(x) is type(y)
    False
    >>> type(x) is opt_cls
    False
    >>> type(y) is opt_cls
    False

    The actual class hierarchy is as follows:
    >>> opt_cls.__bases__ == (Optional,)
    True
    >>> type(x).__bases__ == (opt_cls, Integer)
    True
    >>> type(y).__bases__ == (opt_cls, Void)
    True
    """

    _final = False

    # def __init_subclass__(cls, **kwargs):
    #     bases = cls.__bases__
    #     for index, base in enumerate(bases):
    #         if base is Optional:
    #             break
    #     else:
    #         raise TypeError('Optional class must wrap an existing class')
    #     if index + 1 < len(bases):
    #         wrapped_class = bases[index + 1]
    #         cls.case(TRUE, _=wrapped_class)
    #         cls.default()
    #     else:
    #         raise TypeError('Optional class must wrap an existing class')

    def __new__(cls, *args, **kwargs):
        # Class Optional serves both as a mix-in class for optional classes
        # and as a factory for optional classes.
        # If it is "instantiated" with an existing XDR class, then it
        # creates and returns a new, optional XDR class.
        # In all other cases it is the instantiation of an already
        # existing optional class.
        if not cls._final:
            # class is called to wrap an existing class.
            if kwargs or len(args) != 1 or not inspect.isclass(args[0]) or not issubclass(args[0], XdrType):
                raise TypeError(f"cannot apply Optional class wrapper to {args!s}, {kwargs!s}")
            wrapped_class = args[0]
            if not wrapped_class._final:
                raise TypeError(f"cannot apply Optional class wrapper to "
                                f"unfinished XDR class '{wrapped_class.__name__:s}'")
            optional_class = cls._make_optional_class(wrapped_class)
            return optional_class

        if cls._is_instantiated_as_absent(*args, **kwargs):
            return Void.__new__(cls._absent_class)
        else:
            return cls._original_class.__new__(cls._present_class, *args, **kwargs)

    def encode(self):
        if isinstance(self, Void):
            return FALSE.encode()
        else:
            return TRUE.encode() + super().encode()

    @classmethod
    def parse(cls, source):
        present, source = Boolean.parse(source)
        if present:
            obj, source = cls._original_class.parse(source)
            obj.__class__ = cls._present_class
        else:
            obj = cls._absent_class()
        return obj, source

    @staticmethod
    def _is_instantiated_as_absent(*args, **kwargs):
        return args in ((), (None,)) and not kwargs

    @classmethod
    def _make_optional_class(cls, original_class):
        if issubclass(original_class, Void):
            raise TypeError('Void (sub)class cannot be made optional')
        if issubclass(original_class, Optional):
            return original_class
        optional_class = cls.typedef('*' + original_class.__name__)
        optional_class._original_class = original_class
        optional_class._add_present_class(original_class)
        optional_class._add_absent_class()
        optional_class._abstract = False
        optional_class._final = True
        return optional_class

    @classmethod
    def _add_absent_class(cls):
        absent_class = cls.typedef(cls.__name__, Void)
        cls._absent_class = absent_class

    @classmethod
    def _add_present_class(cls, original_class):
        present_class = cls.typedef(cls.__name__, original_class)
        cls._present_class = present_class

    @classmethod
    def _get_item(cls, name):
        return cls._original_class._get_item(name)

    @classmethod
    def _getattr(cls, name):
        return cls._original_class._getattr(name)

    # def __eq__(self, other):
    #     return super().__eq__(other)
    #
    # def __ne__(self, other):
    #     return super().__ne__(other)
    #
    # def __lt__(self, other):
    #     return super().__lt__(other)
    #
    # def __le__(self, other):
    #     return super().__le__(other)
    #
    # def __gt__(self, other):
    #     return super().__gt__(other)
    #
    # def __ge__(self, other):
    #     return super().__ge__(other)