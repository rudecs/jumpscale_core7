from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo
import JumpScale.grid.grid
import datetime

class mainclass(OSISStoreMongo):
    TTL = 3600 * 24 * 5 # 5 days

    def set(self,key,value,waitIndex=True, session=None):
        db, counter = self._getMongoDB(session)
        dbvalue = db.find_one({'guid': key})
        if dbvalue is not None:
             dbvalue.update(value)
             value = dbvalue
        value['guid'] = key
        value['_ttl'] = datetime.datetime.utcnow()
        value['id'] = key
        db.save(value)
        return [key,True,True]
