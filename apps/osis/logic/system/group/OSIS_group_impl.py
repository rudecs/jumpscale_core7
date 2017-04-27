from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import ObjectNotFound

parentclass = j.core.osis.getOsisImplementationParentClass("system")  # is the name of the namespace

class mainclass(parentclass):

    """
    """
    def getgroup(self, key, session=None):
        if '_' in key:
            gid, _, id = key.partition('_')
            if not gid.isdigit():
                id = key
        else:
            id = key
        return id

    def set(self, key, value, waitIndex=False, session=None):
        oldGroup = None
        if self.exists(value['guid']):
            oldGroup = self.get(value["guid"])
        guid, new, changed = super(parentclass, self).set(key, value, session=session)
        if changed and oldGroup:
            print("OBJECT CHANGED WRITE")
            u = j.core.osis.cmds._getOsisInstanceForCat("system", "user")
            removeList = list(set(oldGroup['users']) - set(value['users']))
            addList = list(set(value['users']) - set(oldGroup['users']))
            if removeList:
                u.updateSearch({'id': {'$in': removeList}}, {'$pull': {'groups': value['id']}})
            if addList:
                u.updateSearch({'id': {'$in': addList}}, {'$push': {'groups': value['id']}})
        return [guid, new, changed]

    def exists(self, key, session=None):
        """
        get dict value
        """
        id = self.getgroup(key, session)
        self.runTasklet('exists', key, session)
        db, counter = self._getMongoDB(session)
        return not db.find_one({"id":id})==None

    def get(self, key, full=False, session=None):
        id = self.getgroup(key, session)
        self.runTasklet('get', key, session)
        db, counter = self._getMongoDB(session)
        res = db.find_one({"id":id})

        # res["guid"]=str(res["_id"])
        if not res:
            raise ObjectNotFound(key)

        if not full:
            res.pop("_id")
            res.pop("_ttl", None)
        return res

    def delete(self, key, session=None):
        id = self.getgroup(key, session)
        client = self.dbclient[self.dbnamespace]
        client.user.update({"groups":id}, {"$pull":{"groups":id}}, multi =  True)
        super(mainclass, self).delete(id, session)
