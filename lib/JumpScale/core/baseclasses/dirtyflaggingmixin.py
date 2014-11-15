
'''Mixin and helpers to access 'dirty flagging' information set by pmtypes'''

DIRTY_PROPERTIES_ATTRIBUTE = '_pm__dirty_properties'
DIRTY_AFTER_LAST_SAVE_ATTRIBUTE = '_pm__dirty_after_last_save'

class DirtyFlaggingMixin:
    """
    Mixin class that will add 2 attributes on the a class containing data about changes to the properties
    """
    def _get_dirty_properties(self):
        '''Return all dirty properties in this instance

        @returns: Dirty property names
        @rtype: set
        '''
        dirty = getattr(self, DIRTY_PROPERTIES_ATTRIBUTE, None)
        if dirty is None: #No if not dirty: not set() == True
            dirty = set()
            setattr(self, DIRTY_PROPERTIES_ATTRIBUTE, dirty)
        return dirty

    '''Check whether a given object got dirty properties

    @type: bool'''
    isDirty = property(fget=lambda s: len(s.dirtyProperties) > 0)

    '''Get a set of all dirtied properties

    @type: set'''
    dirtyProperties = property(fget=_get_dirty_properties)

    '''Check whether a given object was dirtied after last save

    @type: bool'''
    isDirtiedAfterSave = property(fget=lambda s: getattr(s, DIRTY_AFTER_LAST_SAVE_ATTRIBUTE, False))

    def reset_dirtied_after_save(self):
        '''Reset dirtied after save state

        Call this from the function which saves to object to CMDB.
        '''
        setattr(self, DIRTY_AFTER_LAST_SAVE_ATTRIBUTE, False)