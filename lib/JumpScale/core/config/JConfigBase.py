

from JumpScale import j

class ConfiguredItemGroup(object):

    def __init__(self):
       allParamsDict = j.config.getConfig(self._CONFIGTYPE)
       self.__allItemsDict = {}
       for itemname, paramsDict in allParamsDict.iteritems():
           self._pushParamsToItem(itemname, paramsDict)

    def _pushParamsToItem(self, itemname, params, reconfigure=True):
        if itemname in self.__allItemsDict:
            item = self.__allItemsDict[itemname]
        else:
            item = self._ITEMCLASS()
            self.__allItemsDict[itemname] = item
        item._params = params
        item._itemname = itemname
        if reconfigure:
            item._reconfigure()

    def _removeItem(self, itemname):
        self.__allItemsDict[itemname]._remove()
        self.__allItemsDict.pop(itemname)

    def __contains__(self, k):
        return self.__allItemsDict.__contains__(k)

    def __getitem__(self, k):
        return self.__allItemsDict.__getitem__(k)

    def __iter__(self):
        return self.__allItemsDict.__iter__()

    def has_key(self, k):
        return self.__allItemsDict.has_key(k)

    def items(self):
        return self.__allItemsDict.items()

    def iteritems(self):
        return self.__allItemsDict.iteritems()

    def iterkeys(self):
        return self.__allItemsDict.iterkeys()

    def itervalues(self):
        return self.__allItemsDict.itervalues()

    def keys(self):
        return self.__allItemsDict.keys()

    def values(self):
        return self.__allItemsDict.values()


class ConfiguredItem(object):

    def _reconfigure(self):
        pass # Method can be overridden by implementation, but should always be callable from ConfigMgmtBase and ConfigMgmtActionBase

    def _remove(self):
        pass # Method can be overridden by implementation, but should always be callable from ConfigMgmtBase and ConfigMgmtActionBase