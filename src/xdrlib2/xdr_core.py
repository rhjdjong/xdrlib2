# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import numbers
import inspect
import re
import enum
import dis

XDR_UNIT_SIZE = 4
XDR_BYTE_ORDER = 'big'


reserved_names = (
    'bool',
    'case',
    'const',
    'default',
    'double',
    'quadruple',
    'enum',
    'float',
    'hyper',
    'int',
    'opaque',
    'string',
    'struct',
    'switch',
    'typedef',
    'union',
    'unsigned',
    'void',
)


def xdr_padded(bstr):
    return bstr + xdr_padding(len(bstr))


def xdr_padded_size(size):
    return size + xdr_padding_size(size)


def xdr_padding(size):
    return b'\0' * xdr_padding_size(size)


def xdr_padding_size(size):
    return ((XDR_UNIT_SIZE - size % XDR_UNIT_SIZE) % XDR_UNIT_SIZE)


def xdr_remove_padding(bstr, size):
    padded_size = xdr_padded_size(size)
    if len(bstr) < padded_size:
        raise ValueError(f"byte sequence too short. "
                         f"Expected {padded_size:d} bytes, "
                         f"got {len(bstr):d} bytes.")
    if any(b for b in bstr[size:padded_size]):
        raise ValueError(f"non-zero padding byte(s) encountered: {bstr[size:padded_size]!s}'")
    return bstr[:size], bstr[padded_size:]


def xdr_is_valid_name(name):
    if name in reserved_names:
        return False
    return re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name)


_xdr_mode = enum.Enum('_xdr_mode', 'ABSTRACT CONCRETE FINAL')


def _get_assigned_name(frame):
    iterator = iter(dis.get_instructions(frame.f_code))
    for instr in iterator:
        if instr.offset == frame.f_lasti:
            break
    else:
        assert False, "byte code instruction missing"
    assert instr.opname == 'SETUP_WITH'
    instr = next(iterator)
    if instr.opname == 'POP_TOP':
        return None
    return instr.argval


class _MetaXdrType(type):
    # Concrete XDR types contain parameters that determine the
    # allowed values and operations.
    # To prevent inadvertent modifications of these parameters,
    # creating, modifying, or deleting these parameters is not allowed.
    def __setattr__(cls, name, value):
        if cls._mode is _xdr_mode.FINAL:
            raise AttributeError(f"cannot set attribute '{name:s}' to '{value}' for class '{cls.__name__:s}'")
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            cls._setattr_(name, value)

    def __delattr__(cls, name):
        if cls._mode is _xdr_mode.FINAL:
            raise AttributeError(f"cannot delete attribute '{name:s}' from class '{cls.__name__:s}'")
        super().__delattr__(name)

    # Concrete classes expose their parameters as class attributes.
    # Some classes, e.g. structs and unions, also expose their members as class attributes.
    # Name resolution is delegated to the class method '_getattr_' (single underscores).
    def __getattr__(cls, name):
        return cls._getattr_(name)

    # Classes like structs and unions also expose their member types via indexing
    # This operation is delegated to the class method '_getitem_' (single underscores)
    def __getitem__(cls, index):
        return cls._getitem_(index)

    def __enter__(cls):
        if cls._mode is not _xdr_mode.CONCRETE:
            raise TypeError(f"context expression '{cls.__name__:s}' "
                            f"must be an XDR class being constructed")
        frame = inspect.currentframe().f_back
        name = _get_assigned_name(frame)
        cls.__name__ = name
        return cls

    def __exit__(cls, exc_type, exc_value, exc_traceback):
        if cls._mode is not _xdr_mode.FINAL:
            cls._mode = _xdr_mode.FINAL


class XdrType(metaclass=_MetaXdrType):
    _mode = _xdr_mode.ABSTRACT
    _parameters = ()    # Parameters used by an XDR factory class

    # def __init_subclass__(cls, **kwargs):
    #     parameters = cls._get_class_parameters(**kwargs)
    #     if cls._mode is _xdr_mode.FINAL:
    #         if parameters:
    #             raise TypeError(f"cannot subclass final type "
    #                             f"'{cls.__name__:s}' with modifications.")
    #     if cls._mode is _xdr_mode.ABSTRACT:
    #         cls._init_abstract_subclass_(**parameters)
    #     else:
    #         cls._init_concrete_subclass_(**parameters)
    #
    @classmethod
    def _check_parameters_for_completeness(cls, parameters):
        if cls._parameters:
            extra_names = set(parameters.keys()) - set(cls._parameters)
            if extra_names:
                raise ValueError(f"{cls.__name__:s}' subclass got "
                                 f"unexpected parameter(s) {tuple(extra_names)!s}")
        missing_names = set(cls._parameters) - set(parameters.keys())
        return tuple(missing_names)

    @classmethod
    def _init_abstract_subclass_(cls, **kwargs):
        pass

    @classmethod
    def _create_anonymous_subclass(cls, *args, **kwargs):
        if args:
            raise ValueError(f"Cannot instantiate abstract class {cls.__name__:s} for {args!s}")
        return cls.typedef(**kwargs)

    @classmethod
    def _validate_arguments(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def _getattr_(cls, name):
        raise AttributeError(f"'{cls.__class__.__name__:s}' object '{cls.__name__:s}' has no attribute '{name:s}'")

    @classmethod
    def _setattr_(cls, name, value):
        raise AttributeError(f"cannot set attribute '{name:s}' in class '{cls.__name__:s}'")

    def __getattr__(self, name):
        return getattr(self.__class__, name)

    @classmethod
    def _getitem_(cls, index):
        raise TypeError(f"class '{cls.__name__:s}' is not subscriptable")

    @classmethod
    def _get_class_parameters(cls, **kwargs):
        """
        This method obtains the parameters from the class body
        (any attribute that does not start with an underscore)
        and the kwargs parameter in the argument.
        The parameters found in the class body are removed from the body,
        to avoid conflicts with e.g. class properties with the same name.
        """
        cls_vars = vars(cls).copy()
        parameters = {}
        for name, value in cls_vars.items():
            if name in cls._parameters or (not name.startswith('_') and (
                    isinstance(value, (numbers.Number, str)) or
                    (inspect.isclass(value) and issubclass(value, XdrType)))):
                parameters[name] = value
                delattr(cls, name)
        for name in kwargs:
            if name in parameters:
                raise ValueError(f"class '{cls.__name__:s}' got duplicate class parameter '{name:s}'")
        parameters.update(kwargs)
        return parameters

    @classmethod
    def _get_names_from_class_body(cls, *args):
        parameters = {}
        class_body = vars(cls)
        for name, value in class_body.items():
            if not name.startswith('_'):
                if name in parameters:
                    raise ValueError(f"duplicate name '{name:s}' in class '{cls.__name__:s}'")
                parameters[name] = value

        if args:
            unexpected_parameters = set(parameters.keys()) - set(args)
            if unexpected_parameters:
                raise ValueError(f"unexpected parameter(s) for '{cls.__name__:s}': "
                                f"{tuple(unexpected_parameters)!s} ")
        for name in parameters:
            delattr(cls, name)
        return parameters



    @classmethod
    def _init_concrete_subclass_(cls, **kwargs):
        pass

    @classmethod
    def decode(cls, bstr):
        obj, rest = cls.parse(bstr)
        if rest != b'':
            raise ValueError(f"input contains additional data '{rest}'")
        return obj

    @staticmethod
    def _is_valid_xdr_name(name):
        if name in reserved_names:
            return False
        return re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name)

    # def pad(self, bstr):
    #     return bstr + self.padding(len(bstr))
    #
    # def padding(self, size):
    #     return b'\0' * ((4 - size % 4) % 4)
    #
    # def padded_size(self, size):
    #     return size + len(self.padding(size))
    #
    # def remove_padding(self, bstr, size):
    #     if any(b for b in bstr[size:]):
    #         raise ValueError("non-zero padding byte(s) encountered: '{bstr[size:].encode('utf8'):s}'")
    #     return bstr[:size]
    #
    @classmethod
    def typedef(cls, _xdr_type_name=None, *bases, **kwargs):
        type_name = _xdr_type_name if _xdr_type_name else cls.__name__
        new_type = cls.__class__(type_name, (cls,) + bases, {}, **kwargs)
        return new_type


class XdrAtomic(XdrType):
    _mode = _xdr_mode.ABSTRACT

    _packed_size = None

    # def __new__(cls, *args, **kwargs):
    #     if cls._mode is _xdr_mode.ABSTRACT:
    #         raise NotImplementedError(f"cannot instantiate abstract '{cls.__name__:s}' class")
    #     return super().__new__(cls, *args, **kwargs)

    @classmethod
    def _getattr_(cls, name):
        if name == 'packed_size':
            return cls._packed_size
        return super()._getattr_(name)

    @classmethod
    def _validate_arguments(cls, *args, **kwargs):
        pass  # Validation is best done during instance creation.

    # @classmethod
    # def packed_size(cls):
    #     return cls._packed_size


class Void(XdrType):
    _mode = _xdr_mode.FINAL
    # _final = True
    # _abstract = False

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._mode is _xdr_mode.FINAL:
            if parameters:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")

    def __new__(cls, _=None):
        return super().__new__(cls)

    # @classmethod
    # def _validate_arguments(cls):
    #     pass

    def encode(self):
        return b''

    @classmethod
    def parse(cls, bstr):
        return cls(), bstr

    def __eq__(self, other):
        return other is None or isinstance(other, Void)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return f"{self.__class__.__name__:s}()"

    def __str__(self):
        return 'None'
