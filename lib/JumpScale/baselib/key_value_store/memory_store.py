from store import KeyValueStoreBase

NAMESPACES = dict()

class MemoryKeyValueStore(KeyValueStoreBase):

    def __init__(self, namespace=None):
        if namespace:
            self.db = NAMESPACES.setdefault(namespace, dict())
        else:
            self.db = dict()
        KeyValueStoreBase.__init__(self)

    def checkChangeLog(self):
        pass


    def get(self, category, key):
        key=str(key)
        if not self.exists(category, key):
            raise RuntimeError("Could not find object with category %s key %s"%(category,key))
        return self.db[category][key]

    def set(self, category, key, value):
        key=str(key)
        if category not in self.db:
            self.db[category] = dict()

        self.db[category][key] = value

    def delete(self, category, key):
        key=str(key)
        #self._assertExists(category, key)
        if self.exists(category, key):
            del(self.db[category][key])

        if self.db.has_key(category) and not self.db[category]:
            del(self.db[category])

    def exists(self, category, key):
        key=str(key)
        if category in self.db and key in self.db[category]:
            return True
        else:
            return False

    def list(self, category="", prefix=""):
        if category=="":
            res=[]
            for category in self.db.keys():
                res+= [k for k in self.db[category] if k.startswith(prefix)]
            return res
        else:
            self._assertCategoryExists(category)
            return [k for k in self.db[category] if k.startswith(prefix)]

    def listCategories(self):
        return self.db.keys()

    def _categoryExists(self, category):
        return category in self.db
