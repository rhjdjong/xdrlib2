# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

from .xdr_core import XdrType, Void
from .xdr_integer import Integer, UnsignedInteger
from .xdr_enumeration import Enumeration

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

        union datatype switch (integer kind) {
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

    The `datatype.default` method must alwasy be the last method called in this sequence,
    because it locks the subclass against additional modifications.
    To lock the subclass without actually specifying a default arm, use the no-arguments
    form of the method, like `datatype.default()`.

    The class datatype is a subclass of Union:
    >>> issubclass(datatype, Union)
    True

    The subclasses of datatype for a specific switch value are subclasses
    of both datatype and the type associated with the switch value
    >>> casetype = datatype[1]
    >>> issubclass(casetype, datatype)
    True
    >>> issubclass(casetype, Integer)
    True
    >>> casetype.switch
    Integer(1)

    These subclasses can be instantiate with any value that is acceptable
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

    Subclasses can also be retrieved through the name specified for the case.
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

    _final = False
    _abstract = True
    _arm_info = None

    def __init_subclass__(cls, **kwargs):
        # Remove the known 'case', 'default', 'switch' methods and attribute from the parameters
        if cls._final:
            parameters = cls._get_names_from_class_body()
            # No additional parameters should be present.
            # The only subclassing allowed is to define another name for an existing union type.
            if parameters or kwargs:
                raise TypeError('cannot subclass union type with modifications.')
        elif cls._abstract:
            parameters = cls._get_names_from_class_body()
            parameters.update(kwargs)
            # Exactly one parameter should be present.
            # This is the switch name, and its value is the switch type,
            if not parameters:
                raise ValueError(f"switch name and type are required for subclassing a union type")
            if len(parameters) > 1:
                raise ValueError(f"unexpected parameters {parameters!s} for '{cls.__name__:s}' union type.")
            switch_name, switch_type = list(parameters.items())[0]
            cls._switch_name = switch_name
            cls._switch_type = switch_type
            cls._names = super()._names.copy()
            cls._arm_name = {}
            cls._arm_type = {}
            cls._abstract = False
        else:
            # Exactly one parameter should be present.
            # This is arm_info for the concrete union arm class
            parameters = cls._get_names_from_class_body('type')
            parameters.update(kwargs)

            if not parameters:
                raise ValueError(f"unexpected parameters {parameters!s} for '{cls.__name__:s}' union type.")
            cls._parameters = super()._parameters.copy()
            cls._parameters.update(parameters)
            # try:
            #     switch_value = parameters['switch']
            # except KeyError:
            #     raise ValueError(f"class '{cls.__name__:s}' union arm class definition requires 'switch' value")
            # cls._switch_value = switch_value
            # cls._names = {'switch': None}
            cls._final = True

    def __new__(cls, *args, **kwargs):
        if not cls._final:
            raise ValueError(f"cannot instantiate abstract or unfinished union class {cls.__name__:s}'")
        return super().__new__(cls, *args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__:s}[{self.switch:d}]({super().__str__():s})"

    @classmethod
    def _get_item(cls, index):
        index = cls._switch_type(index)
        try:
            arm_class = cls._arm_type[index]
        except KeyError:
            arm_class = cls._arm_type.get('default')
            if arm_class is None:
                raise ValueError(f"invalid switch value '{index}' for union type '{cls.__name__:s}'")
        arm_class._parameters['switch'] = index
        return arm_class

    @classmethod
    def case(cls, *args, **kwargs):
        cls._get_arm_data_from_arguments(*args, **kwargs, default=False)

    @classmethod
    def default(cls, *args, **kwargs):
        if args or kwargs:
            cls._get_arm_data_from_arguments(*args, **kwargs, default=True)
        cls._final = True

    @classmethod
    def _get_arm_data_from_arguments(cls, *args, default=False, **kwargs, ):
        if cls._final:
            raise ValueError(f"cannot add case or default clause to finished union class '{cls.__name__:s}'.")
        if cls._abstract:
            raise ValueError(f"cannot add case or default clause to abstract union class '{cls.__name__:s}'")
        if len(kwargs) > 1:
            raise ValueError(f"class '{cls.__name__:s}': case or default clause "
                             f"requires one 'name=type' or 'Void' argument.")
        if default:
            if len(args) > 1:
                raise ValueError(f"class '{cls.__name__:s}': arm specification requires "
                                 f"a single '<name>=<type>' or 'Void' argument.")
        else:
            if not args:
                raise ValueError(f"class '{cls.__name__:s}': case clause requires one or more switch values.")
        if kwargs:
            arm_name, arm_type = list(kwargs.items())[0]
            if arm_type is Void:
                raise ValueError(f"class '{cls.__name__:s}': Void arm does not allow a name.")
        else:
            arm_name = None
            arm_type = args[-1]
            args = args[:-1]
            if arm_type is not Void:
                raise ValueError(f"class '{cls.__name__:s}': non-Void arm requires a name.")
        if default:
            if args:
                raise ValueError(f"default clause requires a single '<name>=<type>' or 'Void' argument.")
            args = ('default',)
        else:
            if not args:
                raise ValueError(f"case clause requires one or more switch values.")
            args = (cls._switch_type(v) for v in args)

        if arm_name and (arm_name == cls._switch_name or arm_name in cls._names):
            raise ValueError(f"duplicate name '{arm_name:s}' in union class '{cls.__name__:s}'")

        for switch_value in args:
            cls._arm_name[switch_value] = arm_name
            arm_class = cls.typedef(cls.__name__, arm_type, type=arm_type)
            cls._arm_type[switch_value] = arm_class
            if arm_name:
                cls._names[arm_name] = arm_class

    @property
    def switch(self):
        return self._parameters['switch']

    def encode(self):
        return self.switch.encode() + super().encode()

    @classmethod
    def parse(cls, bstr):
        switch, bstr = cls._switch_type.parse(bstr)
        arm_class = cls[switch]
        data, bstr = arm_class._parameters['type'].parse(bstr)
        return arm_class(data), bstr
