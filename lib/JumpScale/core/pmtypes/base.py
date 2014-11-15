

import inspect
import types
import operator

try:
    import ujson as json
except:
    import json

from JumpScale import j
from JumpScale.core.baseclasses.dirtyflaggingmixin import \
        DIRTY_PROPERTIES_ATTRIBUTE, DIRTY_AFTER_LAST_SAVE_ATTRIBUTE

#Needed to handle default values
#We want NO_DEFAULT and NO_VALUE as some special instances because we can't
#use 'None': if we'd use None as discriminator whether a default value is
#provided by a class author/spec writer, it would become impossible to use
#None itself as a default value.
#NO_VALUE is used to check whether a certain attribute is already set. We
#can't use None as a discriminator here as well for the same reason.
NO_DEFAULT = object()
NO_VALUE = object()
#Used as 'ignore' value, which disables call of the internal set_impl in the
#descriptor __set__ when returned from a given fset generator
IGNORE = object()

class BaseType(object):
    '''Base class for all defined types'''

    def __init__(self, default=NO_DEFAULT, check=None, doc=None,
            allow_none=False, flag_dirty=False, fset=None, readonly=False):
        '''Initialize a new typed property

        @param default: Default value
        @type default: object or callable
        @param check: Custom checker callable (func(self, value) -> bool)
        @type check: callable
        @param doc: Docstring for this descriptor
        @type doc: string
        @param allow_none: Allow setting of 'None' as value
        @type allow_none: bool
        @param flag_dirty: Enable dirty flagging for this property
        @type flag_dirty: bool
        @param readonly: Read-only attribute
        @type readonly: bool

        @note: The fset parameter should not be used unless you know how it
               works. See the testcase.
        '''
        #Need this since we want to store all constructor arguments on the
        #object
        varnames, _, _, locals_ = inspect.getargvalues(inspect.currentframe())

        #We don't use None as default since None could be the desired default
        self._default = default
        self._check = check
        self._allow_none = allow_none
        self._flag_dirty = flag_dirty
        self._fset = fset
        self._readonly = readonly

        if doc:
            self.__doc__ = doc

        #Store constructor arguments
        self._constructor_args = dict((name, locals_[name]) \
                                        for name in varnames)

    #__get__, __set__ and __delete__ -> descriptor protocol
    def __get__(self, obj, objtype=None):
        try:
            return getattr(obj, self.attribute_name)
        except AttributeError:
            pass

        if self._default is not NO_DEFAULT:
            value = self.get_default(obj)
            setattr(obj, self.attribute_name, value)
            return value

        raise AttributeError('\'%s\' has no attribute \'%s\'' % \
                             (obj.__class__.__name__, self._name))

    def __set__(self, obj, new_value):
        if self._readonly:
            raise AttributeError('can\'t set attribute: readonly attribute')

        if self._fset:
            helper = self._fset(obj, new_value)
            if not isinstance(helper, types.GeneratorType):
                raise RuntimeError(
                    'fset parameter of BaseType should return a generator')

            real_new_value = helper.next()
            if real_new_value is not IGNORE:
                saved_value = self._set_impl(obj, real_new_value)
            else:
                saved_value = IGNORE

            try:
                helper.send(saved_value)
                helper.next()
            except StopIteration:
                pass
            else:
                raise RuntimeError(
                    'Provided fset generator generates more than one value')
        else:
            self._set_impl(obj, new_value)

    def __delete__(self, obj):
        #TODO Check whether we want dirty flagging here
        #TODO Check with Peter/Kurt -> Should 'logical delete' go in here?
        delattr(obj, self.attribute_name)

    constructor_args = property(fget=lambda s: s._constructor_args)

    def _set_name(self, value):
        self._name = value
        self.attribute_name = '_pm_%s' % value
    _PM_NAME = property(fget=operator.attrgetter('_name'), fset=_set_name)

    def _check_value(self, obj, value):
        '''Check the provided value for this type

        @param value: Value to check
        @type value: object

        @returns: Whether the provided value is valid
        @rtype: bool
        '''
        #If None is allowed, let it pass
        #Other checks could fail otherwise
        if value is None and self._allow_none:
            return True

        #Type-specific check
        if not self.check(value):
            return False

        #Object-class-specific check
        if callable(self._check) and not self._check(obj, value):
            return False

        return True

    def get_default(self, obj):
        '''Get default value for descriptor attribute

        @returns: Default value
        @rtype: object

        @raises RuntimeError: If the (generated or constant) default value is not valid for this type
        '''
        if self._default is not NO_DEFAULT:
            #Check whether default is a callable
            #If it is, execute it providing obj as argument
            #This way default could be something like this:
            # class CallableDefault(BaseType):
            #     def _get_i_square(self):
            #         return self.i ** 2
            #
            #     i = Integer(default=2)
            #     s = Integer(default=_get_i_square)

            if callable(self._default):
                value = self._default(obj)
            else:
                value = self._default
            if not self._check_value(obj, value):
                msg = ('Default value %r of property %s on %s is invalid' % \
                        (value, self._PM_NAME, obj.__class__.__name__))
                j.logger.log(msg, 5)
                raise RuntimeError(msg)

            return value

        return None

    def _set_impl(self, obj, value):
        #Check whether the value is valid
        if not self._check_value(obj, value):
            #Generic error string
            err = '%s property of %s should be a valid %s, %r is not' % \
                    (self._PM_NAME, obj.__class__.__name__,
                            self.__class__.__name__, value)

            raise ValueError(err)

        #Flag the object as dirty, if necessary
        if self._flag_dirty:
            #Check whether new value is not equal to the old one
            current_value = getattr(obj, self.attribute_name, NO_VALUE)
            if current_value is not value:
                dirty_attributes = getattr(obj, DIRTY_PROPERTIES_ATTRIBUTE,
                                            set())
                dirty_attributes.add(self._PM_NAME)

                setattr(obj, DIRTY_PROPERTIES_ATTRIBUTE, dirty_attributes)
                setattr(obj, DIRTY_AFTER_LAST_SAVE_ATTRIBUTE, True)

        #Finally, set the internal attribute to value
        setattr(obj, self.attribute_name, value)

        return value

    @classmethod
    def checkString(cls, s):
        try:
            s = cls.fromString(s)
        except ValueError:
            return False
        return cls.check(s) 

    @classmethod
    def fromString(cls, s):
        return json.loads(s)

    @classmethod
    def toString(cls, s):
        return json.dumps(s)
