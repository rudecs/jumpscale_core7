from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo
import pymongo
import datetime
import time

class mainclass(OSISStoreMongo):
    TTL = 3600

    def set(self, key, value, waitIndex=False, session=None):
        db, _ = self._getMongoDB(session)
        lock = {'_id': key, 'guid': key, '_ttl': datetime.datetime.utcnow()}
        starttime = time.time()
        while time.time() - starttime < value:
            try:
                db.insert(lock)
                return True
            except pymongo.errors.DuplicateKeyError:
                time.sleep(1)
        return False
