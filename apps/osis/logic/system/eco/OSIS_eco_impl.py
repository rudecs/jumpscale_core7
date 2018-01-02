from JumpScale import j
from gevent.pool import Pool
from JumpScale.grid.osis.OSISStoreMongo import OSISStoreMongo


class mainclass(OSISStoreMongo):
    TTL = 3600 * 24 * 5  # 5 days
    def __init__(self, *args, **kwargs):
        super(mainclass, self).__init__(*args, **kwargs)
        self.pool = Pool(1000)

    def set_helper(self, session, value, isList=False):
        if isList:
            for eco in value:
                self.set_helper(session, eco)
            return True
        db, _ = self._getMongoDB(session)
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

    def set(self, key, value, waitIndex=False, session=None):
        if isinstance(value, list):
            self.pool.wait_available()
            self.pool.apply_async(self.set_helper, (session, value, True))
            return None, None, True
        return self.set_helper(session, value)
