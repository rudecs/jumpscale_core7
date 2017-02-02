from JumpScale import j
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo


class mainclass(OSISStoreMongo):
    TTL = 3600 * 24 * 5  # 5 days

    def set(self, key, value, waitIndex=False, session=None):
        db, counter = self._getMongoDB(session)
        count = db.find({"guid": value["guid"]}).count()
        noreraise = value.pop('noreraise', False)
        new = False
        if count == 1:
            if noreraise:
                return value['guid'], new, False
            db.update({'guid': value['guid']},
                      {'$inc': {'occurrences': value['occurrences']},
                       '$set': {'lasttime': value['lasttime'],
                                'errormessage': value['errormessage'],
                                'errormessagePub': value['errormessagePub']}
                       })
        else:
            new = True
            db.save(value)
        return value['guid'], new, True
