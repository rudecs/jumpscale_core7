

from JumpScale.core.config.IConfigBase import ConfigManagementItem, GroupConfigManagement, SingleConfigManagement

def checkItemClass(itemclass):
    import inspect
    if not inspect.isclass(itemclass):
        raise TypeError("ItemGroupClass argument is not a class")
    if not issubclass(itemclass, ConfigManagementItem):
        raise ValueError("Itemclass [%s] is not a ConfigManagementItem" % itemclass.__name__)
    for attr in "CONFIGTYPE", "DESCRIPTION":
        if not hasattr(itemclass, attr):
            raise ValueError("Itemclass [%s] is invalid: no attribute [%s] found" % (itemclass.__name__, attr))


def ItemGroupClass(itemclass):
    checkItemClass(itemclass)

    class GroupClass(GroupConfigManagement):
        _ITEMCLASS = itemclass
        _CONFIGTYPE = itemclass.CONFIGTYPE
        _DESCRIPTION = itemclass.DESCRIPTION
        if hasattr(itemclass, 'SORT_PARAM'):
            _SORT_PARAM = itemclass.SORT_PARAM
        if hasattr(itemclass, 'KEYS'):
            _KEYS = itemclass.KEYS
        if hasattr(itemclass, 'SORT_METHOD'):
            _SORT_METHOD = itemclass.SORT_METHOD
        
    return GroupClass


def ItemSingleClass(itemclass):
    checkItemClass(itemclass)

    class SingleClass(SingleConfigManagement):
        _ITEMCLASS = itemclass
        _CONFIGTYPE = itemclass.CONFIGTYPE
        _DESCRIPTION = itemclass.DESCRIPTION

    return SingleClass