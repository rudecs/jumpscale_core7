# <License type="Sun Cloud BSD" version="2.2">
#
# Copyright (c) 2005-2009, Sun Microsystems, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. Neither the name Sun Microsystems, Inc. nor the names of other
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SUN MICROSYSTEMS, INC. "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SUN MICROSYSTEMS, INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# </License>

'''Common classes for descriptors

A descriptor is a new-style class functionality which allows one to create
custom properties (actually 'property' is an implementation of a descriptor).

Descriptors can provide 3 special methods: __get__, __set__ and __delete___,
which are executed when the corresponding action (getattr, setattr, delattr)
is performed on an instance of a class using the descriptor.

Here's a sample, which implements the functionality of the builtin 'property':

class Property(object):
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self._fget = fget
        self._fset = fset
        self._fdel = fdel

        self.__doc__ = doc

    def __get__(self, obj, obj_type=None):
        if not self._fget:
            raise AttributeError('Can\'t read property')
        return self._fget(obj)

    def __set__(self, obj, value):
        if not self._fset:
            raise AttributeError('Can\'t set property')
        self._fset(obj, value)

    def __delete__(self, obj):
        if not self._fdel:
            raise AttributeError('Can\t' delete property')
        self._fdel(obj)


Some interesting links:
 * http://users.rcn.com/python/download/Descriptor.htm
 * http://gulopine.gamemusic.org/2007/nov/23/python-descriptors-part-1-of-2/
'''

class BaseDescriptor(property):
    '''Base class for pmtypes descriptors

    This class performs pmtypes checks on __set__. It expects the
    corresponding pmtype to be set as PMTYPE attribute on class level.
    '''

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, check=None):
        '''Initializer for pmtypes descriptors

        All arguments are the same arguments you'd provide to the builtin
        'property' descriptor. The extra C{check} parameter allows one to add
        an extra custom check callable.

        @param fget: Executed on getattr
        @type fget: callable
        @param fset: Executed on setattr
        @type fset: callable
        @param fdel: Executed on delattr
        @type fdel: callable
        @param doc: Documentation for the attribute
        @type doc: string
        @param check: Extra check function (f(self, value))
        @type check: callable
        '''
        property.__init__(self, fget=fget, fset=fset, fdel=fdel, doc=doc)
        if check and not callable(check):
            raise ValueError('check argument should be a callable')
        self._check = check

    def __set__(self, obj, value):
        if not self.PMTYPE.check(value):
            raise ValueError('Invalid value for type %s: %r' % \
                    (self.PMTYPE.__name__, value))
        if self._check and not self._check(obj, value):
            raise ValueError('Invalid value for property, invalidated by custom check method')

        property.__set__(self, obj, value)