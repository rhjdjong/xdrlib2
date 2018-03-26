# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import inspect

from .xdr_core import XdrType, Void, _xdr_mode
from .xdr_enumeration import Boolean, FALSE, TRUE


def _opt_new_present(cls, *args, **kwargs):
    return cls._wrapped_class.__new__(cls, *args, **kwargs)

def _opt_new_absent(cls, *args, **kwargs):
    return Void.__new__(cls, *args, **kwargs)


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
    _mode = _xdr_mode.ABSTRACT
    # _final = False
    # _abstract = True
    _class_for_instances = {}
    _wrapped_class = None
    _parameters = ('optional',)
    _optional_level = 0

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._mode is _xdr_mode.FINAL:
            if parameters:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
        try:
            wrapped_class = parameters.pop('optional')
        except KeyError:
            raise TypeError(f"missing class parameters 'optional' "
                            f"for class '{cls.__name__:s}'")
        if parameters:
            raise ValueError(f"unexpected parameters {parameters!s} for '{cls.__name__:s}' optional type.")
        if cls._mode is _xdr_mode.ABSTRACT:
            cls._init_abstract_subclass_(wrapped_class)
        else:
            cls._init_concrete_subclass_(wrapped_class)

    @classmethod
    def _init_abstract_subclass_(cls, wrapped_class):
        if issubclass(wrapped_class, Void):
            raise TypeError(f"Void (sub)class '{wrapped_class.__name__:s}' cannot be made optional")
        if issubclass(wrapped_class, Optional):
            cls._optional_level = wrapped_class._optional_level + 1
            cls._wrapped_class = wrapped_class._wrapped_class
            absent_base_class = wrapped_class._class_for_instances[False]
            present_base_class = wrapped_class._class_for_instances[True]
        else:
            cls._optional_level = 1
            cls._wrapped_class = wrapped_class
            absent_base_class = Void
            present_base_class = wrapped_class
        cls._mode = _xdr_mode.CONCRETE
        absent_class = cls.typedef(None, absent_base_class, optional=Void)
        present_class = cls.typedef(None, present_base_class, optional=cls._wrapped_class)
        cls._class_for_instances = {False: absent_class, True: present_class}
        cls._mode = _xdr_mode.FINAL

    @classmethod
    def _init_concrete_subclass_(cls, wrapped_class):
        cls._wrapped_class = wrapped_class
        # w = wrapped_class
        # while isinstance(w, Optional):
        #     w = w._class_for_instances[True]
        # cls._wrapped_class = w
        # cls.__new__ = staticmethod(_opt_new)
        cls._mode = _xdr_mode.FINAL

    # def __init_subclass__(cls, **kwargs):
    #     parameters = cls._get_class_parameters(**kwargs)
    #     if cls._final:
    #         if parameters:
    #             raise TypeError(f"cannot subclass optional type '{cls.__name__:s}' with modifications.")
    #     elif cls._abstract:
    #         # This is the optional base class, the parent of the 'present' and 'absent' classes
    #         # It requires one parameter, the class that is being made optional,
    #         if not parameters:
    #             raise ValueError(f"concrete class required for creating a '{cls.__name__:s}' optional type")
    #         if len(parameters) > 1:
    #             raise ValueError(f"unexpected parameters {parameters!s} for '{cls.__name__:s}' optional type.")
    #         extra_names = set(parameters.keys()) - set(cls._parameters)
    #         if extra_names:
    #             raise ValueError(f"{cls.__name__:s}' subclass got unexpected parameter(s) {tuple(extra_names)!s}")
    #         wrapped_class = parameters['optional']
    #         cls._abstract = False
    #         absent_class = cls.typedef(None, Void, optional=Void)
    #         present_class = cls.typedef(None, wrapped_class, optional=wrapped_class)
    #         cls._class_for_instances = [absent_class, present_class]
    #         cls._instanceclass = False # So that __new__ can figure out what is being instantiated.
    #     else:
    #         # This is a subclass for the 'present' or 'absent' casee.
    #         cls._instanceclass = True
    #         cls._optional_class = parameters['optional']
    #     cls._final = True
        # cls._final = True
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
        if cls._mode is _xdr_mode.ABSTRACT:
        # if cls._class_for_instances:
            # No classes for absent or present are defined yet.
            # This class is called to wrap an existing class.
            if kwargs or len(args) != 1 or not inspect.isclass(args[0]) or not issubclass(args[0], XdrType):
                raise TypeError(f"cannot apply Optional class wrapper to {args!s}, {kwargs!s}")
            wrapped_class = args[0]
            # if wrapped_class._abstract:
            #     raise TypeError(f"cannot apply Optional class wrapper to "
            #                     f"abstract XDR class '{wrapped_class.__name__:s}'")
            optional_class = cls.typedef('*' + wrapped_class.__name__, optional=wrapped_class)

            # optional_class._class_for_instances[TRUE] = optional_class.typedef(None, wrapped_class)
            # optional_class._class_when_absent = optional_class.typedef(None, Void)
            # optional_class = cls._make_optional_class(wrapped_class)
            # optional_class._final = True
            return optional_class

        # if cls._instanceclass:
        #     return cls._optional_class.__new__(cls, *args, **kwargs)
        # else:
        is_present = cls._is_instantiated_as_present(*args, **kwargs)
        instance_class = cls._class_for_instances[is_present]
        # if is_present and not kwargs and len(args) == 1 and isinstance(args[0], instance_class._wrapped_class):
        #     return args[0]
        instance = instance_class._wrapped_class.__new__(instance_class, *args, **kwargs)
        return instance

    def encode(self):
        if isinstance(self, Void):
            return FALSE.encode()
        return b''.join(TRUE.encode() for _ in range(self._optional_level)) + super().encode()
        # if isinstance(self, Void):
        #     return FALSE.encode()
        # else:
        #     return TRUE.encode() + super().encode()

    @classmethod
    def parse(cls, source):
        for _ in range(cls._optional_level):
            present, source = Boolean.parse(source)
            if not present:
                break
        instance_class = cls._class_for_instances[present]
        obj, source = instance_class._wrapped_class.parse(source)
        return cls(obj), source

    @staticmethod
    def _is_instantiated_as_present(*args, **kwargs):
        return not (args in ((), (None,)) and not kwargs)

    # @classmethod
    # def _make_optional_class(cls, original_class):
    #     if issubclass(original_class, Void):
    #         raise TypeError('Void (sub)class cannot be made optional')
    #     if issubclass(original_class, Optional):
    #         return original_class
    #     optional_class = cls.typedef('*' + original_class.__name__)
    #     optional_class._original_class = original_class
    #     optional_class._add_present_class(original_class)
    #     optional_class._add_absent_class()
    #     optional_class._abstract = False
    #     optional_class._final = True
    #     return optional_class
    #
    # @classmethod
    # def _add_absent_class(cls):
    #     absent_class = cls.typedef(cls.__name__, Void)
    #     cls._absent_class = absent_class
    #
    # @classmethod
    # def _add_present_class(cls, original_class):
    #     present_class = cls.typedef(cls.__name__, original_class)
    #     cls._present_class = present_class
    #
    # @classmethod
    # def _get_item(cls, name):
    #     return cls._original_class._get_item(name)
    #
    # @classmethod
    # def _getattr(cls, name):
    #     return cls._original_class._getattr(name)

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
