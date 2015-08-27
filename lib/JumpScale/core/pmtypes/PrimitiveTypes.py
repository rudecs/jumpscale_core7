

'''Definition of several primitive type properties (integer, string,...)'''

from JumpScale.core.pmtypes.base import BaseType

class Boolean(BaseType):
    '''Generic boolean type'''
    NAME = 'boolean'

    @staticmethod
    def fromString(s):
        if isinstance(s, bool):
            return s

        s = str(s)
        if s.upper() in ('0', 'FALSE'):
            return False
        elif s.upper() in ('1', 'TRUE'):
            return True
        else:
            raise ValueError("Invalid value for boolean: '%s'" % s)

    @staticmethod
    def checkString(s):
        try:
            Boolean.fromString(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def toString(boolean):
        return str(boolean)

    @staticmethod
    def check(value):
        '''Check whether provided value is a boolean'''
        return value is True or value is False

class Integer(BaseType):
    '''Generic integer type'''
    NAME = 'integer'


    @staticmethod
    def checkString(s):
        return s.isdigit()

    @staticmethod
    def check(value):
        '''Check whether provided value is an integer'''
        return isinstance(value, int)

class Float(BaseType):
    '''Generic float type'''
    NAME = 'float'

    @staticmethod
    def checkString(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def check(value):
        '''Check whether provided value is a float'''
        return isinstance(value, float)

class String(BaseType):
    '''Generic string type'''
    NAME = 'string'

    @staticmethod
    def fromString(s):
        return s

    @staticmethod
    def toString(v):
        return v

    @staticmethod
    def check(value):
        '''Check whether provided value is a string'''
        return isinstance(value, (str, unicode))
