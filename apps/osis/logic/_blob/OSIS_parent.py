from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo
ujson = j.db.serializers.getSerializerType('j')


class mainclass(OSISStoreMongo):

    """
    Defeault object implementation
    """

    def set(self, key, value, waitIndex=False, session=None):
        import bson
        db, counter = self._getMongoDB(session)
        if self.exists(key, session=session):
            changed = True
            new = False
        else:
            changed = False
            new = True
        key = key.replace('-', '')
        dbval = {"_id": key, "guid": key, "value": bson.Binary(value)}
        db.save(dbval)
        return [key, new, changed]

    def get(self, key, full=False, session=None):
        val = OSISStoreMongo.get(self, key, full, session=session)
        return val['value']

