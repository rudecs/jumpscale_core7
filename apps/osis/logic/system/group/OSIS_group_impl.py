from JumpScale import j

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
        guid, new, changed = super(parentclass, self).set(key, value, session=session)

        if changed:
            print("OBJECT CHANGED WRITE")
            u = j.core.osis.cmds._getOsisInstanceForCat("system", "user")
            for user in value['users']:
                userkey = "%s_%s" % (value['gid'], user)
                if u.exists(userkey, session=session) == False:
                    # group does not exist yet, create
                    usernew = u.getObject()
                    usernew.id = user
                    usernew.gid = value['gid']
                    usernew.domain = value['domain']
                    usernew.groups = [value['id']]
                    userguid, a, b = u.set(usernew.guid, usernew.__dict__, session=session)
                else:
                    user = u.get(userkey, session=session)
                    if value['id'] not in user['groups']:
                        user['groups'].append(value['id'])
                        u.set(user['guid'], user, session=session)

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
            j.errorconditionhandler.raiseBug(message="Key %s doesn't exist" % key, level=4)

        if not full:
            res.pop("_id")
            res.pop("_ttl", None)
        return res

    def delete(self, key, session=None):
        id = self.getgroup(key, session)
        client = self.dbclient[self.dbnamespace]
        client.user.update({"groups":id}, {"$pull":{"groups":id}}, multi =  True)
        super(mainclass, self).delete(id, session)

        

