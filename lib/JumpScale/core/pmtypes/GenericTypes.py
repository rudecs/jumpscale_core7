

'''Some jumpscale descriptor types acting as generics

The types defined in this module are no real descriptors, it are functions
which generate descriptor types on-the-fly. The end-user syntax remains
the same:

>>> class MyType: pass
...
>>> from JumpScale.core.baseclasses import BaseType
>>> class MyClass(BaseType):
...     mt = j.basetype.object(MyType)
...
>>> instance = MyClass()
>>> print instance.mt
None
>>> instance.mt = MyType()
>>> instance.mt = 'String is no MyType'
------------------------------------------------------------
Traceback (most recent call last):
    ...
<type 'exceptions.ValueError'>: mt property of MyClass should be a valid MyTypeType, 'String is no MyType' is not

'''
import inspect

from JumpScale.core.pmtypes.base import BaseType as TypeBaseType, NO_DEFAULT

OBJECT_DESCRIPTOR_CACHE = dict()
def Object(type_, **kwargs):
    '''Generic descriptor generator for custom object types

    You should be aware this is, unlike non-generic basetypes, a function
    generating a class instance, not a class.

    @param type_: Type of which values should be instances
    @type type_: class or type
    @param kwargs: Kwargs sent to L{jumpscale.pmtypes.base.BaseType.__init__}

    @returns: An instance of a custom descriptor class
    @rtype: L{jumpscale.pmtypes.base.BaseType.__init__}

    @see: L{jumpscale.pmtypes.base.BaseType.__init__}
    '''
    if not inspect.isclass(type_) and not isinstance(type_, type):
        raise TypeError('type_ parameter of Object should be of type type or class')

    #Cache created descriptors so we can do type checks (if ever needed)
    if type_ in OBJECT_DESCRIPTOR_CACHE:
        return OBJECT_DESCRIPTOR_CACHE[type_](**kwargs)

    class ObjectType(TypeBaseType):
        __doc__ = 'Generic %s type' % type_.__name__

        #This needs to be a classmethod since we need to know the required type
        #and got no 'self' to store it
        @classmethod
        def check(cls, value):
            '''Check whether provided value is an instance of the required type'''
            return isinstance(value, cls._type)

    #Use nicer names
    ObjectType.__name__ = '%sType' % type_.__name__
    #Store required type at classlevel
    ObjectType._type = type_

    OBJECT_DESCRIPTOR_CACHE[type_] = ObjectType

    return ObjectType(**kwargs)

#qtypename should be set so we can hook on j.basetype.
Object.qtypename = 'object'


ENUMERATION_DESCRIPTOR_CACHE = dict()
def Enumeration(enumerationtype, **kwargs):
    '''Generic descriptor generator for custom enumeration types

    You should be aware this is, unlike non-generic basetypes, a function
    generating a class instance, not a class.

    @param enumerationtype: Type of which values should be instances
    @type enumerationtype: Subclass of L{jumpscale.baseclasses.BaseEnumeration.BaseEnumeration}
    @param kwargs: Kwargs sent to L{jumpscale.pmtypes.base.BaseType.__init__}

    @returns: An instance of a custom descriptor class
    @rtype: L{jumpscale.pmtypes.base.BaseType.__init__}

    @see: L{jumpscale.pmtypes.base.BaseType.__init__}
    '''
    from JumpScale.core.baseclasses import BaseEnumeration
    if not issubclass(enumerationtype, BaseEnumeration):
        raise TypeError('enumerationtype parameter of Object should be of type type or class')

    #Cache created descriptors so we can do type checks (if ever needed)
    if enumerationtype in ENUMERATION_DESCRIPTOR_CACHE:
        return ENUMERATION_DESCRIPTOR_CACHE[enumerationtype](**kwargs)

    class EnumerationType(TypeBaseType):
        __doc__ = 'Generic %s type' % enumerationtype.__name__

        #This needs to be a classmethod since we need to know the required type
        #and got no 'self' to store it
        @classmethod
        def fromString(cls, s):
            try:
                return cls._type.getByName(s)
            except KeyError:
                raise ValueError("Invalid value for %s: '%s'" % (cls.__name__, s))

        @classmethod
        def toString(cls, val):
            return str(val)

        @classmethod
        def check(cls, value):
            '''Check whether provided value is an instance of the required type'''
            if isinstance(value, basestring):
                try:
                    cls._type.getByName(value)
                except KeyError:
                    return False
                else:
                    return True

            return cls._type.check(value)

        def __get__(self, obj, objtype=None):
            name = TypeBaseType.__get__(self, obj, objtype)
            return self._type.getByName(name)

        def __set__(self, obj, value):
            #Catch __str__ overrides
            if not isinstance(value, self._type):
                value = str(value)
            else:
                value = value._pm_enumeration_name

            return TypeBaseType.__set__(self, obj, value)

    #Use nicer names
    EnumerationType.__name__ = '%sType' % enumerationtype.__name__
    #Store required type at classlevel
    EnumerationType._type = enumerationtype

    ENUMERATION_DESCRIPTOR_CACHE[enumerationtype] = EnumerationType

    return EnumerationType(**kwargs)

#qtypename should be set so we can hook on j.basetype.
Enumeration.qtypename = 'enumeration'