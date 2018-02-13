from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo


class mainclass(OSISStoreMongo):

    """
    Defeault object implementation
    """
    def __init__(self, *args, **kwargs):
        super(mainclass, self).__init__(*args, **kwargs)

    def set(self, key, value, waitIndex=False, session=None):
        db, counter = self._getMongoDB(session)
        dbval = {"_id": key, "guid": key, "value": value}
        db.save(dbval)
        return key

    def get(self, key, full=False, session=None):
        try:
            val = OSISStoreMongo.get(self, key, full, session=session)
            return val['value']
        except:
            return None

    def delete(self, key, session=None):
        self.runTasklet('delete', key, session)
        db, counter = self._getMongoDB(session)
        try:
            res = OSISStoreMongo.get(self, key, True, session=session)
            db.remove(res["_id"])
        except KeyError:
            pass