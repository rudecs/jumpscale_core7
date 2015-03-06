from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo

class mainclass(OSISStoreMongo):

    """
    Default object implementation
    """
    def set(self, key, value, waitIndex=False, session=None):
        db, counter = self._getMongoDB(session)
        if key and self.exists(key, session=session):
            orig = self.get(key, True, session=session)
            orig.update(value)
            value = orig
            changed = True
            new = False
        else:
            value['_id'] = key
            changed = False
            new = True
        db.save(value)
        return [key, new, changed]

    def get(self, key, full=False, session=None):
        self.runTasklet('get', key, session)
        db, counter = self._getMongoDB(session)
        return db.find_one(key)
