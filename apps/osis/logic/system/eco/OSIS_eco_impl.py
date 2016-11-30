from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo


class mainclass(OSISStoreMongo):
    TTL = 3600 * 24 * 5  # 5 days

    def set(self, key, value, waitIndex=False, session=None):
        db, counter = self._getMongoDB(session)
        count = db.find({"guid": value["guid"]}).count()
        new = False
        if count == 1:
            db.update({'guid': value['guid']},
                      {'$inc': {'occurrences': value['occurrences']},
                       '$set': {'lasttime': value['lasttime']}
                       })
        else:
            new = True
            db.save(value)
        return value['guid'], new, True
