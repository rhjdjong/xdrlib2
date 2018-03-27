# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType, Void, _xdr_mode
from .xdr_integer import Integer, UnsignedInteger
from .xdr_optional import Optional

import collections.abc


class Union(XdrType):
    """
    Union.typedef(<subtype-name>, <switch-name>=<switch-type>) --> Union with switch <switch-name> of type <switch-type>
    UnionType.case(<switch-value>+, <name>=<type>) --> Adds a subtype to Union subclass for the indicated switch value
    UnionType.case(<switch-value>+, Void) --> Adds a Void subtype to Union for the indicated switch value
    UnionType.default(<name>=<type>) --> Adds a default subtype to the Union
    UnionType.default(Void) --> Adds a default Void subtype to the Union
    UnionType(<switch-value>) --> Union subtype for the indicated switch value
    UnionType(<switch-value>)(<data>) --> Union subtype instance for the indicated switch type

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

    >>> from xdrlib2 import Union, String, Boolean, Void
    >>> datatype = Union.typedef('datatype', kind=Integer)

    The various union arms are defined via the 'case' and 'default' methods on the derived class
    >>> datatype.case(1, number=Integer)
    >>> datatype.case(2, 3, text=String)
    >>> datatype.case(4, flag=Boolean)
    >>> datatype.default(Void)

    The `UnionWithDefault.default` method must always be the last method called in this sequence,
    because it locks the subclass against additional modifications.
    To lock the subclass without actually specifying a default arm, use the no-arguments
    form of the method, like `UnionWithDefault.default()`.

    The class UnionWithDefault is a subclass of Union:
    >>> issubclass(datatype, Union)
    True

    The subclasses of UnionWithDefault for a specific switch value are subclasses
    of both UnionWithDefault and the type associated with the switch value
    >>> casetype = datatype[1]
    >>> issubclass(casetype, datatype)
    True
    >>> issubclass(casetype, Integer)
    True
    >>> casetype.switch
    Integer(1)

    These subclasses can be instantiated with any value that is acceptable
    for the type associated with the union arem
    >>> casevalue = casetype(15)
    >>> isinstance(casevalue, datatype)
    True
    >>> isinstance(casevalue, Integer)
    True
    >>> casevalue.switch
    Integer(1)
    >>> casevalue.kind
    Integer(1)

    Subclasses can also be retrieved through the name specified for the arm.
    Note though that in the case where multiple switch values are mapped to
    the same arm (as is the case for the 'text' arm in this example), the
    switch value that is associated with the subtype can be any of the specified
    switch values.
    >>> casetype = datatype.text
    >>> issubclass(casetype, datatype)
    True
    >>> issubclass(casetype, String)
    True
    >>> casetype.switch in (2, 3)
    True
    """

    _mode = _xdr_mode.ABSTRACT
    _union_parameters = {}

    def __init_subclass__(cls, **kwargs):
        parameters = cls._get_class_parameters(**kwargs)
        if cls._mode is _xdr_mode.FINAL:
            if parameters:
                raise TypeError(f"cannot subclass final type "
                                f"'{cls.__name__:s}' with modifications.")
        if cls._mode is _xdr_mode.ABSTRACT:
            cls._init_abstract_subclass_(**parameters)
        else:
            cls._init_concrete_subclass_(**parameters)

    @classmethod
    def _init_abstract_subclass_(cls, **kwargs):
        existing_union_parameters = cls._union_parameters
        cls._union_parameters = {}
        cls._union_parameters.update(existing_union_parameters)

        # Exactly one keyword should be present.
        # This is the switch name, and its value is the switch type,
        if not kwargs:
            raise ValueError(f"switch name and type are required for subclassing a union type")
        if len(kwargs) > 1:
            raise ValueError(f"unexpected parameters {kwargs!s} for '{cls.__name__:s}' union type.")
        switch_name, switch_type = list(kwargs.items())[0]
        if not issubclass(switch_type, (Integer, UnsignedInteger)):
            raise TypeError(f"invalid switch type '{switch_type.__name__:s}' "
                            f"for union subclass '{cls.__name__:s}.'")
        cls._union_parameters['switch_name'] = switch_name
        cls._union_parameters['switch_type'] = switch_type
        cls._union_parameters['arm_name'] = {}
        cls._union_parameters['arm_type'] = {}
        cls._union_parameters['switch_by_name'] = {}
        cls._union_parameters['arm_info'] = {}
        cls._mode = _xdr_mode.CONCRETE

    @classmethod
    def _init_concrete_subclass_(cls, **kwargs):
        # This is arm_info for the concrete union arm class
        # parameters should contain keyword 'type'
        basis_parameters = cls._union_parameters
        cls._union_parameters = {}
        cls._union_parameters.update(basis_parameters)
        if len(kwargs) > 1:
            extra_names = set(kwargs.keys()) - {'type'}
            raise ValueError(f"unexpected parameters {extra_names!s} for '{cls.__name__:s}' union arm type.")
        try:
            arm_type = kwargs['type']
        except KeyError:
            raise ValueError(f"missing parameter 'type' for '{cls.__name__:s}' union arm type.")

        cls._union_parameters['arm_info'] = {
            'name': None,
            'type': arm_type,
            'switch': None
        }
        cls._mode = _xdr_mode.FINAL

    # @classmethod
    # def _prepare_for_optional_use(cls, optional_class):
    #     optional_class._union_parameters = cls._union_parameters.copy()
    #     for index, arm_type in cls._union_parameters['arm_type']:
    # def __init_subclass__(cls, **kwargs):
    #     # Remove the known 'case', 'default', 'switch' methods and attribute from the parameters
    #     if cls._final:
    #         parameters = cls._get_names_from_class_body()
    #         # No additional parameters should be present.
    #         # The only subclassing allowed is to define another name for an existing union type.
    #         if parameters or kwargs:
    #             raise TypeError('cannot subclass union type with modifications.')
    #     elif cls._abstract:
    #         parameters = cls._get_names_from_class_body()
    #         parameters.update(kwargs)
    #         # Exactly one parameter should be present.
    #         # This is the switch name, and its value is the switch type,
    #         if not parameters:
    #             raise ValueError(f"switch name and type are required for subclassing a union type")
    #         if len(parameters) > 1:
    #             raise ValueError(f"unexpected parameters {parameters!s} for '{cls.__name__:s}' union type.")
    #         switch_name, switch_type = list(parameters.items())[0]
    #         cls._union_switch_name = switch_name
    #         cls._union_switch_type = switch_type
    #         cls._names = super()._names.copy()
    #         cls._union_arm_name = {}
    #         cls._union_arm_type = {}
    #         cls._abstract = False
    #     else:
    #         # Exactly one parameter should be present.
    #         # This is arm_info for the concrete union arm class
    #         parameters = cls._get_names_from_class_body('type')
    #         parameters.update(kwargs)
    #
    #         if not parameters:
    #             raise ValueError(f"unexpected parameters {parameters!s} for '{cls.__name__:s}' union type.")
    #         cls._parameters = super()._parameters.copy()
    #         cls._parameters.update(parameters)
    #         # try:
    #         #     switch_value = parameters['switch']
    #         # except KeyError:
    #         #     raise ValueError(f"class '{cls.__name__:s}' union arm class definition requires 'switch' value")
    #         # cls._switch_value = switch_value
    #         # cls._names = {'switch': None}
    #         cls._final = True

    @classmethod
    def _getattr_(cls, name):
        try:
            return cls._union_parameters[name]
        except KeyError:
            pass
        try:
            index = cls._union_parameters['switch_by_name'][name]
        except KeyError:
            pass
        else:
            return cls._getitem_(index)
        return super()._getattr_(name)

    def __getattr__(self, name):
        if name in ('switch', self._union_parameters['switch_name']):
            return self._union_parameters['arm_info']['switch']
        elif name == self._union_parameters['arm_info']['name']:
            return self
        else:
            return super().__getattr__(name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in ('switch', self.switch_name):
            if self.arm_type(value) is self.__class__:
                self.arm_info['switch'] = value
            else:
                raise AttributeError(f"attribute '{name:s}' of '{self.__class__.__name__:s}' "
                                     f"object cannot be written.") from None
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        if name.startswith('_'):
            super().__delattr__(name)
        elif name in ('switch', self.switch_name):
            self.arm_info['switch'] = None
        else:
            super().__delattr__(name)

    def __new__(cls, *args, **kwargs):
        if cls._mode is _xdr_mode.ABSTRACT:
            if not kwargs:
                raise NotImplementedError(f"cannot instantiate abstract class '{cls.__name__:s}'")
            return cls.typedef(**kwargs)
        if not cls._mode is _xdr_mode.FINAL:
            raise NotImplementedError(f"cannot instantiate unfinished union class '{cls.__name__:s}'")
        return super().__new__(cls, *args, **kwargs)

    # def __new__(cls, *args, **kwargs):
    #     if not cls._final:
    #         raise ValueError(f"cannot instantiate abstract or unfinished union class {cls.__name__:s}'")
    #     return super().__new__(cls, *args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__:s}[{self.switch:d}]({super().__str__():s})"

    @classmethod
    def _getitem_(cls, index):
        index = cls.switch_type(index)
        arm_class = cls.arm_type.get(index)
        arm_name = cls.arm_name.get(index)
        if arm_class is None:
            arm_class = cls.arm_type.get('default')
            arm_name = cls.arm_name.get('default')
        if arm_class is None:
            raise ValueError(f"invalid switch value '{index}' for union type '{cls.__name__:s}'")

        arm_class.arm_info['switch'] = index
        arm_class.arm_info['name'] = arm_name
        return arm_class

    @classmethod
    def case(cls, *args, **kwargs):
        if cls._mode is _xdr_mode.FINAL and len(args) == 1 and not kwargs:
            case_value = args[0]
            arm_class = cls.arm_type.get(case_value)
            arm_name = cls.arm_name.get(case_value)
            if arm_class is None:
                raise ValueError(f"invalid discriminant value {case_value!s} for {cls.__name__:s}' union class")
            return arm_name, arm_class
        else:
            cls._create_arm_data_from_arguments(*args, **kwargs, default=False)

    @classmethod
    def default(cls, *args, **kwargs):
        if cls._mode is _xdr_mode.FINAL and not args and not kwargs:
            arm_class = cls.arm_type.get('default')
            arm_name = cls.arm_name.get('default')
            if arm_class is None:
                raise ValueError(f"'{cls.__name__:s}' union class "
                                 f"does not have a default arm")
            return arm_name, arm_class
        if args or kwargs:
            cls._create_arm_data_from_arguments(*args, **kwargs, default=True)
        cls._mode = _xdr_mode.FINAL

    @classmethod
    def _create_arm_data_from_arguments(cls, *args, default=False, **kwargs, ):
        if cls._mode is not _xdr_mode.CONCRETE:
            raise ValueError(f"cannot add case or default clause to "
                             f"{cls._mode.lower():s} union class '{cls.__name__:s}'.")
        if len(kwargs) > 1:
            raise ValueError(f"class '{cls.__name__:s}': case or default clause "
                             f"requires one 'name=type' or 'Void' argument.")
        if default:
            if len(args) > 1:
                raise ValueError(f"class '{cls.__name__:s}': default arm specification requires "
                                 f"a single '<name>=<type>' or 'Void' argument.")
        else:
            if not args:
                raise ValueError(f"class '{cls.__name__:s}': case clause requires one or more switch values.")
        if kwargs:
            arm_name, arm_type = list(kwargs.items())[0]
        else:
            arm_name = None
            arm_type = args[-1]
            args = args[:-1]
        if default:
            if args:
                raise ValueError(f"default clause requires a single '<name>=<type>' or 'Void' argument.")
            args = ('default',)
        else:
            if not args:
                raise ValueError(f"case clause requires one or more switch values.")
            args = tuple((cls.switch_type(v) for v in args))

        if arm_name and (arm_name == cls.switch_name or arm_name in cls.switch_by_name):
            raise ValueError(f"duplicate name '{arm_name:s}' in union class '{cls.__name__:s}'")

        if issubclass(arm_type, cls):
            if not issubclass(arm_type, Optional):
                raise TypeError(f"infinite recursion '{arm_name:s}={arm_type.__name__:s}' "
                                f"for class '{cls.__name__:s}'")
        elif arm_type._mode is not _xdr_mode.FINAL:
            raise TypeError(f"abstract or unfinished class '{arm_name:s}={arm_type.__name__:s}' "
                            f"for class '{cls.__name__:s}'")
        # Create a new subclass that is also a subclass of the arm type
        arm_class = cls.typedef(f"{cls.__name__:s}[{','.join(str(a) for a in args)}]", arm_type, type=arm_type)
        for switch_value in args:
            cls.arm_name[switch_value] = arm_name
            cls.arm_type[switch_value] = arm_class
            if arm_name:
                cls.switch_by_name[arm_name] = switch_value

    # @property
    # def switch(self):
    #     return self._parameters['switch']

    def encode(self):
        return self.switch.encode() + super().encode()

    @classmethod
    def parse(cls, bstr):
        switch, bstr = cls.switch_type.parse(bstr)
        arm_class = cls[switch]
        data, bstr = super(Union, arm_class).parse(bstr)
        return data, bstr
