from JumpScale import j

parentclass=j.core.osis.getOsisImplementationParentClass("system")  #is the name of the namespace
import bson

class mainclass(parentclass):
    """
    """

    def set(self,key,value,waitIndex=False, session=None):
        guid, new, changed = super(parentclass, self).set(key, value, session=session)

        g=j.core.osis.cmds._getOsisInstanceForCat("system","group")
        if changed:
            for group in value['groups']:
                grkey="%s_%s"%(value['gid'],group)
                if g.exists(grkey, session=session)==False:
                    #group does not exist yet, create
                    grnew=g.getObject()
                    grnew.id=group
                    grnew.gid=value['gid']
                    grnew.domain=value['domain']
                    grnew.users=[value['id']]
                    grguid,a,b=g.set(grnew.guid,grnew.__dict__, session=session)
                else:
                    gr=g.get(grkey, session=session)
                    if value['id'] not in gr['users']:
                         gr['users'].append(value['id'])
                         g.set(gr['guid'],gr, session=session)
        return guid, new, changed

    def exists(self, key, session=None):
        """
        get dict value
        """
        gid, _, id = key.partition('_')
        self.runTasklet('exists', key, session)
        db, counter = self._getMongoDB(session)
        return not db.find_one({"id":id})==None

    def get(self, key, full=False, session=None):
        if '_' in key:
            gid, _, id = key.partition('_')
            if not gid.isdigit():
                id = key
        else:
            id = key
        self.runTasklet('get', key, session)
        db, counter = self._getMongoDB(session)
        res=db.find_one({"id":id})

        # res["guid"]=str(res["_id"])
        if not res:
            j.errorconditionhandler.raiseBug(message="Key %s doesn't exist" % key, level=4)

        if not full:
            res.pop("_id")
            res.pop("_ttl", None)
        return res
