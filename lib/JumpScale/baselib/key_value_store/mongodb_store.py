from .store import KeyValueStoreBase
from JumpScale import j

import pymongo
from pymongo import MongoClient



import ujson as json
import time

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

class MongoDBKeyValueStore(KeyValueStoreBase):
    osis = dict()

    def __init__(self,namespace="",host='localhost',port=7771,db=0,password='', serializers=[],masterdb=None, changelog=True):
        raise RuntimeError("not implemented")
        self.namespace = namespace

        self.db = MongoClient()

        KeyValueStoreBase.__init__(self, [])


    def get(self, category, key):
        categoryKey = self._getCategoryKey(category, key)

        value = self.redisclient.get(categoryKey)
        return self.unserialize(value)

    def set(self, category, key, value,expire=0):
        """
        @param expire is in seconds when value will expire
        """
        if j.basetype.dictionary.check(value):
            if "guid" in value:
                guid=value.pop("guid")
                value["_id"]=guid
            # value = json.dumps(value)
            categoryKey = self._getCategoryKey(category, key)
            # from IPython import embed
            # print "DEBUG NOW set"
            # embed()
            
            self.redisclient.set(categoryKey, value)
        else:
            raise RuntimeError("Only support dicts in set")

    def delete(self, category, key):
        if self.hasmaster:
            self.writedb.delete(category,key)
            self.addToChangeLog(category, key,action='D')
        else:
            categoryKey = self._getCategoryKey(category, key)
            # self._assertExists(categoryKey)
            self.redisclient.delete(categoryKey)

    def exists(self, category, key):
        categoryKey = self._getCategoryKey(category, key)
        return self.redisclient.exists(categoryKey)

    def list(self, category, prefix):
        prefix = "%s:" % category
        lprefix = len(prefix)
        fullkeys = self.redisclient.keys("%s*" % prefix)
        keys = list()
        for key in fullkeys:
            keys.append(key[lprefix:])
        return keys

    def listCategories(self):
        return list(self.categories.keys())

    def _getCategoryKey(self, category, key):
        return '%s:%s' % (category, key)

    def _stripCategory(self, keys, category):
        prefix = category + "."
        nChars = len(prefix)
        return [key[nChars:] for key in keys]

    def _categoryExists(self, category):
        categoryKey = self._getCategoryKey(category, "")
        return bool(self._client.prefix(categoryKey, 1))
