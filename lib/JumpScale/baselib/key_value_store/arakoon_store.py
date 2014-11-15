from store import KeyValueStoreBase
from JumpScale import j

import JumpScale.baselib.serializers

class ArakoonKeyValueStore(KeyValueStoreBase):

    def __init__(self, namespace=None, serializers=None):
        KeyValueStoreBase.__init__(self, serializers)
        self._client = j.clients.arakoon.getClient(namespace)
        self.categories = dict()
        if not self.exists("dbsystem", "categories"):
            self.set("dbsystem", "categories", {})
        self.categories=self.get("dbsystem", "categories")

    def checkChangeLog(self):
        pass

    def get(self, category, key):
        #self._assertExists(category, key)

        categoryKey = self._getCategoryKey(category, key)
        value = self._client.get(categoryKey)
        return self.unserialize(value)

    def set(self, category, key, value, JSModelSerializer=None):
        if category not in self.categories:
            self.categories[category]=True
            self.set("dbsystem", "categories", self.categories)
        categoryKey = self._getCategoryKey(category, key)
        self._client.set(categoryKey, self.serialize(value))

    def delete(self, category, key):
        self._assertExists(category, key)

        categoryKey = self._getCategoryKey(category, key)
        self._client.delete(categoryKey)

    def exists(self, category, key):
        categoryKey = self._getCategoryKey(category, key)
        return self._client.exists(categoryKey)

    def list(self, category, prefix):
        categoryKey = self._getCategoryKey(category, prefix)
        fullKeys = self._client.prefix(categoryKey)
        return self._stripCategory(fullKeys, category)

    def increment(self, incrementtype):
        """
        @param incrementtype : type of increment is in style machine.disk.nrdisk  (dot notation)
        """
        client = self._client
        key = self._getCategoryKey("increment", incrementtype)
        if not client.exists(key):
            client.set(key, "1")
            incr=1
        else:
            rawOldIncr = client.get(key)
            if not rawOldIncr.isdigit():
                raise ValueError("Increment type %s does not have a digit value: %s" % (incrementtype, rawOldIncr))
            while True:
                oldIncr = int(rawOldIncr)
                incr = oldIncr + 1
                oldval = client.testAndSet(key, rawOldIncr, str(incr))
                if oldval == rawOldIncr:
                    break
                rawOldIncr = oldval
        return incr

    def listCategories(self):
        return self.categories.keys()

    def _stripKey(self, catKey):
        if "." not in catKey:
            raise ValueError("Could not find the category separator in %s" %catKey)
        return catKey.split(".", 1)[0]

    def _getCategoryKey(self, category, key):
        return str('%s.%s' % (category, key))

    def _stripCategory(self, keys, category):
        prefix = category + "."
        nChars = len(prefix)
        return [key[nChars:] for key in keys]

    def _categoryExists(self, category):
        categoryKey = self._getCategoryKey(category, "")
        return bool(self._client.prefix(categoryKey, 1))
