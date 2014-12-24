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

    def get(self, key, full=False, session=None):
        """
        @return as json encoded
        """
        val = parentclass.get(self, key, full, session=session)
        # if val is not None and 'passwd' in val:

        #     val['passwd'] = j.core.osis.decrypt(val['passwd'])
        return val

