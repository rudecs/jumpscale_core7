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

class DirtyFlaggingProperty(property):
    """
    This property, if used in combination with an object inheriting from 'DirtyObjectMixin' 
    will flag the object as dirty if the value of the attribute is set
    """
    def __init__(self, propname, checkType = None, *args, **kwargs):
        """
        Contstructor for this property
        
        @param propname : the name of the property
        @param checktype : the j.basetype type class that can be used for type validation of the value
        """
        self._propname = propname
        self._checkType = checkType

    def __get__(self, obj, objtype=None):
        """
        Return the value of the attribute
        """
        return getattr(obj, '_%s' % self._propname)

    def __set__(self, obj, value):
        """
        Sets the value of the attribute.
        If a checktype class is supplied, the check() mathod on this class will be executed to validate the supplied value.
        """
        if value == getattr(obj, '_%s' % self._propname):
            return
        
        if value is not None and self._checkType and callable(self._checkType.check) and not self._checkType.check(value):
            raise TypeError("The type of the value for '%s' is invalid."%self._propname)
        d = getattr(obj, '_dirtied', set())
        if not self._propname in d:
            d.add(self._propname)
            
        obj._dirtied = d
        setattr(obj, '_%s' % self._propname, value)


class DirtyObjectMixin:
    """
    Mixin class that will add 2 attributes on the a class containing data about changes to the properties
    isDirty  : will return true is the list of dirtyProperties contains items
    dirtyProperties : contains the set of updated properties
    """
    def _get_dirty_properties(self):
        '''Return all dirty properties in this instance

        @returns: Dirty property names
        @rtype: set
        '''
        dirty = getattr(self, '_dirtied', None)
        if dirty is None: #No if not dirty: not set() == True
            dirty = set()
            self._dirtied = dirty
        return dirty

    isDirty = property(fget=lambda s: len(s.dirtyProperties) > 0)
    dirtyProperties = property(fget=_get_dirty_properties)