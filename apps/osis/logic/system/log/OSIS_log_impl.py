from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo
import JumpScale.grid.grid
import uuid
import datetime

ujson = j.db.serializers.getSerializerType('j')

class mainclass(OSISStoreMongo):
    TTL = 3600 * 24 * 5 # 5 days
    """
    """

    def set(self,key,value,waitIndex=False, session=None):
        db, counter = self._getMongoDB(session)
        ttl = datetime.datetime.utcnow()
        if len(value)>0:
            for log in value:
                log['_ttl'] = ttl
        db.insert(value)
        return ["",True,True]

    def destroyindex(self):
        raise NotImplementedError()
        
    destroy=destroyindex


    def getIndexName(self):
        return "system_log"

    def get(self,key, session=None):
        j.errorconditionhandler.raiseBug(message="osis get for log not implemented",category="osis.notimplemented")
        #work with elastic search only

    def exists(self,key, session=None):
        j.errorconditionhandler.raiseBug(message="osis exists for log not implemented",category="osis.notimplemented")
        #work with elastic search only


    #NOT IMPLEMENTED METHODS WHICH WILL NEVER HAVE TO BE IMPLEMENTED

    def setObjIds(self,**args):
        j.errorconditionhandler.raiseBug(message="osis method setObjIds is not relevant for logger namespace",category="osis.notimplemented")

    def rebuildindex(self,**args):
        j.errorconditionhandler.raiseBug(message="osis method rebuildindex is not relevant for logger namespace",category="osis.notimplemented")

    def list(self,**args):
        j.errorconditionhandler.raiseBug(message="osis method list is not relevant for logger namespace",category="osis.notimplemented")


