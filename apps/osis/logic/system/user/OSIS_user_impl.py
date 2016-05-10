from JumpScale import j

parentclass=j.core.osis.getOsisImplementationParentClass("system")  #is the name of the namespace
import bson

class mainclass(parentclass):
    """
    """
    def getuser(self, key, session=None):
        if '_' in key:
            gid, _, id = key.partition('_')
            if not gid.isdigit():
                id = key
        else:
            id = key
        return id


    def set(self,key,value,waitIndex=False, session=None):
        g=j.core.osis.cmds._getOsisInstanceForCat("system","group")

        for group in value['groups']:
            grkey="%s_%s"%(value['gid'],group)
            if g.exists(grkey, session=session)==False:
                raise ValueError("Group %s doesn't exist is grid %s"%(group, value['gid']))

        guid, new, changed = super(parentclass, self).set(key, value, session=session)

        if changed:
            for group in value['groups']:
                gr=g.get(grkey, session=session)
                if value['id'] not in gr['users']:
                     gr['users'].append(value['id'])
                     g.set(gr['guid'],gr, session=session)
        return guid, new, changed

    def exists(self, key, session=None):
        """
        get dict value
        """
        id = self.getuser(key, session)
        self.runTasklet('exists', key, session)
        db, counter = self._getMongoDB(session)
        return not db.find_one({"id":id})==None

    def get(self, key, full=False, session=None):
        id = self.getuser(key , session)
        self.runTasklet('get', key, session)
        db, counter = self._getMongoDB(session)
        res=db.find_one({"id":id})
        # res["guid"]=str(res["_id"])
        if not res:
            raise KeyError(key)

        if not full:
            res.pop("_id")
            res.pop("_ttl", None)
        return res


    def delete(self, key, session=None):
        id = self.getuser(key, session)
        client = self.dbclient[self.dbnamespace]
        client.group.update({"users":id}, {"$pull":{"users":id}}, multi = True)
        super(mainclass, self).delete(id, session)




