

from JumpScale import j

from JumpScale import j
from JumpScale.core.pmtypes.base import BaseType as TypeBaseType

def generate_init_properties(cls, attrs):
    '''Generate a class __init_properties__ method

    @param cls: Type to generate method for
    @type cls: type
    @param attrs: Class construction attributes
    @type attrs: dict

    @returns: __init_properties__ method
    @rtype: method
    '''
    def __init_properties__(self):
        '''Initialize all properties with their default value'''

        # Call superclass __init_properties__, if any. No-op otherwise
        base = super(cls, self)
        if hasattr(base, '__init_properties__'):
            base.__init_properties__()

        for name, attr in (p for p in attrs.iteritems() \
                            if isinstance(p[1], TypeBaseType)):
            value = attr.get_default(self)
            setattr(self, attr.attribute_name, value)

    return __init_properties__


class BaseTypeMeta(type):
    '''Meta class for all BaseTypes, makes sure we know the name of descriptor attributes'''

    def __new__(cls, name, bases, attrs):
        t = type.__new__(cls, name, bases, attrs)

        try:
            #If this *is* 'BaseObject' we don't want to do anything special with it
            #This raises a NameError if BaseObject is not 'known' yet
            BaseType
        except NameError:
            return t

        # Store attribute name on BaseType attributes
        for name, value in (p for p in attrs.iteritems() \
                            if isinstance(p[1], TypeBaseType)):
            value._PM_NAME = name

        #Generate __init_properties__
        ip = generate_init_properties(t, attrs)
        setattr(t, '__init_properties__', ip)

        property_metadata = dict()
        for base in bases:
            property_metadata.update(
                getattr(base, 'pm_property_metadata', dict()))
        for name, value in (p for p in attrs.iteritems() \
                            if isinstance(p[1], TypeBaseType)):
            property_metadata[name] = value.constructor_args

        setattr(t, 'pm_property_metadata', property_metadata)

        return t


class BaseType(object):

    __metaclass__ = BaseTypeMeta

    def __init__(self):
        """
        Initialize basetype
        
        During initialization all pmtype properties are set to their default
        values. This is only done when an object is created for the first time,
        otherwise the property values would be overwritten when e.g. restoring
        an object from the cmdb.        
        """
        
        if not hasattr(self, '_pm__initialized'):
            self.__init_properties__()
        self._pm__initialized = True
        