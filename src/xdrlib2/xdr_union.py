# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType, xdr_mode
from .xdr_enumeration import Enumeration, Boolean
from .xdr_void import Void
from .xdr_integer import Integer, UnsignedInteger

import copy


class Union(XdrType):
    """
    Union.typedef(<subtype-name>, <switch-name>=<switch-type>) --> Union with switch <switch-name> of type <switch-type>
    UnionType.case(<switch-value>+, [<name>=]<type>) --> Adds a subtype to Union subclass for the indicated switch value
    UnionType.case(<switch-value>+, [<name>=]Void) --> Adds a Void subtype to Union for the indicated switch value
    UnionType.default([<name>=]<type>) --> Adds a default subtype to the Union
    UnionType.default([<name>=]Void) --> Adds a default Void subtype to the Union
    UnionType(<switch-value, <data>) --> Union subtype instance for the indicated switch value
    UnionTypeInstance.switch --> value of the switch for the union subtype instance
    UnionTypeInstance.name --> arm name for the union subtype instance (None of no name is defined)

    Union is a fairly complex type, with several levels of instantiation.
    The first step of instantiation is to create a concrete subclass of the xdrlib.Union type,
    by specifying the switch name and type.

    The following example implements the XDR specification

        union UnionWithDefault switch (integer kind) {
        case 1:
            integer number;
        case 2, 3:
            string text;
        case 4:
            boolean flag;
        default:
            void;
        }

    >>> from xdrlib2 import Union, Integer, String, Boolean, Void
    >>> datatype = Union.typedef('datatype', kind=Integer)

    The various union arms are defined via the 'case' and 'default' methods on the derived class
    >>> datatype.case(1, number=Integer)
    >>> datatype.case(2, 3, text=String)
    >>> datatype.case(4, flag=Boolean)
    >>> datatype.default(Void)

    The `.default` method must always be the last method called in this sequence,
    because it locks the subclass against additional modifications.
    To lock the subclass without actually specifying a default arm, use the no-arguments
    form of the method, like `UnionWithDefault.default()`.

    Another way to define a union is by using the 'with' statement:
    >>> with Union.typedef('MyUnion', kind=Integer) as MyUnion:
    >>>     MyUnion.case(1, number=Integer)
    >>>     MyUnion.case(2, flag=Boolean)

    Again, the '.default' method must be called last. With this method, however,
    it is not required to call the '.default' method to lock the class.
    Instead, the class is locked automatically at the end of the 'with' suite.
    This method is the only way to define a self-referential union type, where an arm
    has the union itself as its arm type.

    Union classes can be instantiated by specifying a switch value
    followed by any arguments required by the arm's class:
    >>> x = datatype(4, True)
    """

    _mode = xdr_mode.ABSTRACT
    _union_parameters = {
        'switch_name': None,
        'switch_type': None,
        'arm_type': None,
        'arm_name': None,
        'arm_switch': None,
        'arm_cache': None
    }
    _switch = None
    _type = None
    _name = None

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._mode in (xdr_mode.FINAL, xdr_mode.CONCRETE):
            if parameters:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
            return

        # Exactly one keyword should be present.
        # This is the switch name, and its value is the switch type,
        if not parameters:
            raise ValueError(f"switch name and type are required for subclassing a union type")
        if len(parameters) > 1:
            raise ValueError(f"only one paramaeter allowed for '{cls.__name__:s}' union type. Got {kwargs!s}")
        switch_name, switch_type = parameters.popitem()
        if not issubclass(switch_type, (Integer, UnsignedInteger)):
            raise TypeError(f"invalid switch type '{switch_type.__name__:s}' "
                            f"for union subclass '{cls.__name__:s}.'")

        existing_union_parameters = cls._union_parameters
        cls._union_parameters = existing_union_parameters.copy()
        cls._union_parameters['switch_name'] = switch_name
        cls._union_parameters['switch_type'] = switch_type
        cls._union_parameters['arm_type'] = {}
        cls._union_parameters['arm_name'] = {}
        cls._union_parameters['arm_switch'] = {}
        cls._union_parameters['arm_cache'] = {}
        cls._mode = xdr_mode.CONCRETE

    @classmethod
    def _case(cls, *args, **kwargs):
        switch_values, arm_name, arm_type = cls._get_arm_data(*args, **kwargs)
        if not switch_values:
            raise TypeError(f"class '{cls.__name__:s}': case clause requires one or more switch values.")
        cls._create_arm(switch_values, arm_name, arm_type)

    @classmethod
    def default(cls, *args, **kwargs):
        if args or kwargs:
            switch_values, arm_name, arm_type = cls._get_arm_data(*args, **kwargs)
            if switch_values:
                raise TypeError(f"class '{cls.__name__:s}': default arm specification requires "
                                f"a single '<name>=<type>' or 'Void' argument.")
            switch_values = ['default']
            cls._create_arm(switch_values, arm_name, arm_type)
        cls._mode = xdr_mode.FINAL

    @staticmethod
    def _get_arm_data(*args, **kwargs):
        if kwargs:
            # called with ([switch_value, ..., switch_value,] armname=armtype)
            if len(kwargs) > 1:
                raise TypeError(f"class '{cls.__name__:s}': case or default clause "
                                f"requires one 'name=type' or 'Void' argument.")
            arm_name, arm_type = kwargs.popitem()
            switch_values = args
        else:
            # called with ([switch_value, ..., switch_value,] armtype)
            if not args:
                raise TypeError(f"class '{cls.__name__:s}': case or default clause "
                                f"requires one 'name=type' or 'Void' argument.")
            arm_type = args[-1]
            arm_name = None
            switch_values = args[:-1]
        return switch_values, arm_name, arm_type


    @classmethod
    def _create_arm(cls, switch_values, arm_name, arm_type):
        if cls._mode is not xdr_mode.CONCRETE:
            raise TypeError(f"cannot add case or default clause to "
                            f"{cls._mode.lower():s} union class '{cls.__name__:s}'.")

        if arm_name and (arm_name == cls._union_parameters['switch_name'] or
                         arm_name in cls._union_parameters['arm_switch']):
            raise ValueError(f"duplicate name '{arm_name:s}' in union class '{cls.__name__:s}'")

        try:
            if not issubclass(arm_type, XdrType):
                raise TypeError
            if arm_type._mode is xdr_mode.ABSTRACT:
                raise TypeError
        except TypeError:
            raise TypeError(f"cannot use {arm_type!s} as variant type in union") from None

        for switch in switch_values:
            if switch in cls._union_parameters['arm_type']:
                raise TypeError(f"duplicate switch value '{switch!s}' for union '{cls.__name__:s}'")
            cls._union_parameters['arm_type'][switch] = arm_type
            cls._union_parameters['arm_name'][switch] = arm_name
            if arm_name is not None:
                cls._union_parameters['arm_switch'].setdefault(arm_name, switch)

    @classmethod
    def _getitem_(cls, index):
        if cls._mode is not xdr_mode.FINAL:
            raise NotImplementedError(f"cannot get subclass from non-final union class '{cls.__name__:s}'")
        arm_class = cls._get_arm_subclass(index)
        return arm_class

    @classmethod
    def _getattr_(cls, name):
        # Attribute 'case' on the class refers to the 'case' method to define an arm.
        # This is different from the attribute 'case' on the instance which refers to the
        # specific arm that has been instantiated.
        if name == 'case':
            return cls._case
        else:
            try:
                return cls._union_parameters[name]
            except KeyError:
                return super()._getattr_(name)

    @classmethod
    def _get_arm_subclass(cls, index):
        arm_class = cls._make_union_arm_subclass(index)
        arm_class._init_gets_switch_value = False
        return arm_class

    @classmethod
    def _get_arm_type_data(cls, index):
        switch_value = cls._union_parameters['switch_type'](index)
        for sw in (switch_value, 'default'):
            arm_type = cls._union_parameters['arm_type'].get(sw)
            arm_name = cls._union_parameters['arm_name'].get(sw)
            if arm_type is not None:
                break
        else:
            raise ValueError(f"invalid switch value '{switch_value!s}' "
                             f"for union class '{cls.__name__:s}'")
        return switch_value, arm_type, arm_name

    def __new__(cls, discr, *args, **kwargs):
        if cls._mode is not xdr_mode.FINAL:
            raise NotImplementedError(f"cannot get subclass from non-final union class '{cls.__name__:s}'")

        switch_value, arm_type, arm_name = cls._get_arm_type_data(discr)
        if not kwargs and len(args) == 1 and isinstance(args[0], arm_type):
            arm_instance = copy.copy(args[0])
        else:
            arm_instance = arm_type(*args, **kwargs)
        cls.update_class(arm_instance, arm_name, switch_value)
        return arm_instance

    def _eq_class(self, other):
        if not isinstance(other, Union):
            return False
        if self.union is not other.union:
            return False
        return self.switch == other.switch

    @classmethod
    def update_class(cls, arm_instance, arm_name, switch_value):
        arm_cls = arm_instance.__class__.typedef(f"{cls.__name__:s}[{switch_value!s}]")
        arm_cls._xdr_parameters = arm_cls._xdr_parameters.copy()
        arm_cls._xdr_parameters['switch'] = switch_value
        arm_cls._xdr_parameters['type'] = arm_instance.__class__
        arm_cls._xdr_parameters['case'] = arm_name
        arm_cls._xdr_parameters['union'] = cls

        def _enc(s):
            return arm_cls.switch._encode_() + super(arm_cls, s)._encode_()

        arm_cls._encode_ = _enc
        arm_cls._decode_ = classmethod(cls._decode_.__func__)
        arm_cls._eq_class = cls._eq_class

        def _get_class_attr(s, name):
            try:
                return s._xdr_parameters[name]
            except KeyError:
                pass

            try:
                return s.union._union_parameters[name]
            except KeyError:
                return super(arm_cls, s)._getattr_(name)
        arm_cls._getattr_ = classmethod(_get_class_attr)

        def _get_inst_attr(s, name):
            try:
                return super(arm_cls, s).__getattr__(name)
            except AttributeError:
                pass

            try:
                return getattr(s.__class__, name)
            except KeyError:
                raise AttributeError(f"'{s.__class__.__name__:s}' object "
                                     f"has no attribute '{name:s}'") from None
        arm_cls.__getattr__ = _get_inst_attr

        if issubclass(cls, Optional):
            arm_cls.__name__ = cls.__name__

            def _repr(s):
                return super(arm_cls, s).__repr__()

            def _str(s):
                return super(arm_cls, s).__str__()
        else:
            def _repr(s):
                name = s.case
                if name:
                    value_str = f"{name:s}={super(arm_cls, s).__str__():s}"
                else:
                    value_str = super(arm_cls, s).__str__()
                return f"{s.__class__.__name__:s}({value_str:s})"

            def _str(s):
                return f"{{{arm_cls.switch!s}:{super(arm_cls, s).__str__():s}}}"

        arm_cls.__repr__ = _repr
        arm_cls.__str__ = _str

        def _eq(s, other):
            if s is other:
                return True
            if isinstance(other, Union) and not(Union._eq_class(s, other)):
                return False
            return super(arm_cls, s).__eq__(other)

        arm_cls.__eq__ = _eq

        def _ne(s, other):
            return not s == other

        arm_cls.__ne__ = _ne
        cls.register(arm_cls)
        arm_instance.__class__ = arm_cls

    @classmethod
    def _decode_(cls, bstr):
        switch, bstr = cls._union_parameters['switch_type']._decode_(bstr)
        sw_value, arm_type, arm_name = cls._get_arm_type_data(switch)
        element_value, bstr = arm_type._decode_(bstr)
        return cls.__new__(cls, sw_value, element_value), bstr


class Optional(Union, opted=Boolean):
    _mode = xdr_mode.ABSTRACT
    _parameters = ('wrapped',)

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        existing_union_parameters = cls._union_parameters
        cls._union_parameters = existing_union_parameters.copy()
        if not parameters:
            return

        extra_names = parameters.keys() - cls._parameters
        if extra_names:
            raise TypeError(f"unexpected class parameter(s) {extra_names!s} for class '{cls.__name__:s}'")
        wrapped_class = parameters['wrapped']
        cls._union_parameters['arm_type'] = {}
        cls._union_parameters['arm_name'] = {}
        cls._union_parameters['arm_switch'] = {}
        cls._union_parameters['arm_cache'] = {}
        with cls as c:
            c.case(False, Void)
            c.case(True, element=wrapped_class)
        cls._mode = xdr_mode.FINAL

    def __new__(cls, *args, **kwargs):
        # Class Optional serves both as a base class for optional classes
        # and as a factory for optional classes.
        #
        # If the abstract base class is "instantiated" with an existing XDR class,
        # then it creates and returns a new, concrete, derived optional XDR class.
        if cls._mode in (xdr_mode.ABSTRACT, xdr_mode.CONCRETE):
            if len(args) != 1 or len(kwargs) != 0:
                raise TypeError(f"invalid arguments for Optional class wrapper: {args!r}, {kwargs!r}")
            wrapped_class = args[0]
            try:
                if not issubclass(wrapped_class, XdrType):
                    raise TypeError
                if issubclass(wrapped_class, Void):
                    raise TypeError
            except TypeError:
                raise TypeError(f"cannot apply Optional class wrapper to {wrapped_class!s}") from None

            optional_class = cls.typedef('*' + wrapped_class.__name__, wrapped=wrapped_class)
            return optional_class

        # In all other cases it is the instantiation of an already
        # existing optional class.
        # The arguments determine if it is instantiated as present or absent.
        is_present = cls._is_instantiated_as_present(*args, **kwargs)
        arm_instance = super().__new__(cls, is_present, *args, **kwargs)
        return arm_instance

    @classmethod
    def _decode_(cls, bstr):
        present, bstr = cls._union_parameters['switch_type']._decode_(bstr)
        sw_value, arm_type, arm_name = cls._get_arm_type_data(present)
        element_value, bstr = arm_type._decode_(bstr)
        return super().__new__(cls, present, element_value), bstr

    @staticmethod
    def _is_instantiated_as_present(*args, **kwargs):
        if kwargs:
            return True
        if not args:
            return False
        if len(args) == 1 and args[0] is None:
            return False
        return True

    # @classmethod
    # def _make_union_arm_subclass(cls, index):
    #     switch_value, arm_type, arm_name = cls._get_arm_type_data(index)
    #     return UnionArm.typedef(cls.__name__, arm_type,
    #                             switch=switch_value, arm_name=arm_name, union=cls, type=arm_type)
    #     # arm_class = cls.typedef(cls.__name__, arm_type)
    #     # arm_class._switch = switch_value
    #     # arm_class._type = arm_type
    #     # arm_class._type = arm_name
    #     # arm_class._union = cls
    #     # arm_class.__repr__ = cls._repr
    #     # arm_class.__str__ = cls._str
    #     # arm_class.__new__ = cls._new
    #     # arm_class.__init__ = cls._init
    #     return arm_class

    @classmethod
    def _getattr_(cls, name):
        if cls._mode is xdr_mode.FINAL:
            # Assume that the instance is present
            _, arm_type, _ = cls._get_arm_type_data(True)
            return cls(arm_type._getattr_(name))
        else:
            return super()._getattr_(name)

    @classmethod
    def _getitem_(cls, index):
        if cls._mode is xdr_mode.FINAL:
            # Assume that the instance is present
            _, arm_type, _ = cls._get_arm_type_data(True)
            # return arm_type._getitem_(index)
            if issubclass(arm_type, Enumeration):
                return cls(arm_type._getitem_(index))
            else:
                return arm_type._getitem_(index)
        else:
            return super()._getitem_(index)



