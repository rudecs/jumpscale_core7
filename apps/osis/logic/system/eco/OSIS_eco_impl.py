from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo


class mainclass(OSISStoreMongo):
    TTL = 3600 * 24 * 5  # 5 days

    def set(self, key, value, waitIndex=False, session=None):
        db, counter = self._getMongoDB(session)
        objectindb = db.find_one({"guid": value["guid"]})
        if objectindb:
            objectindb.update(value)
            value = objectindb
        noreraise = value.pop('noreraise', False)
        self.setPreSave(value, session)
        new = False
        if objectindb:
            if noreraise:
                return value['guid'], new, False
            db.update({'guid': value['guid']},
                      {'$inc': {'occurrences': value['occurrences']},
                       '$set': {'lasttime': value['lasttime'],
                                'errormessage': value['errormessage'],
                                'errormessagePub': value['errormessagePub'],
                                'state': value['state']}
                       })

        else:
            new = True
            db.save(value)
        return value['guid'], new, True
