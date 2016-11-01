from JumpScale import j
from JumpScale.grid.osis.OSISStore import OSISStore
import imp
import ujson as json
import pymongo
import datetime


def _changekey(object, map):
    if isinstance(object, dict):
        for key, value in object.iteritems():
            if isinstance(key, basestring):
                object.pop(key)
                for old, new in map.iteritems():
                    key = key.replace(old, new)
                object[key] = value
            object[key] = _changekey(value, map)
    elif isinstance(object, list):
        for idx, value in enumerate(object):
            object[idx] = _changekey(value, map)
    return object

def cleankeys(object):
    return _changekey(object, {'$': '\u0024', '.': '\u002e'})

def restorekeys(object):
    return _changekey(object, {'\u0024': '$', '\u002e': '.'})

class OSISStoreMongo(OSISStore):
    MULTIGRID = True
    TTL = 0

    """
    Default object implementation for mongodbserver
    NEW:
    - powerfull search capabilities
    - more consistent way of working with id's & guid's

    """
    def __init__(self, dbconnections):
        self.dbclient = dbconnections['mongodb_main']

    def _getDB(self):
        raise RuntimeError("Not Implemented")

    def _getMongoDB(self, session):
        if not session.gid in self._db:
            if not self.MULTIGRID:
                dbnamespace = '%s_%s' % (session.gid, self.dbnamespace)
            else:
                dbnamespace = self.dbnamespace
            client = self.dbclient[dbnamespace]
            db = client[self.categoryname]
            counter = client["counter"]

            if self.TTL != 0:
                db.ensure_index('_ttl', expireAfterSeconds=self.TTL)
            self._db[session.gid] = db, counter
        return self._db[session.gid]

    def init(self, path, namespace, categoryname):
        """
        gets executed when catgory in osis gets loaded by osiscmds.py (.init method)
        """

        self._db = dict()
        if namespace == 'system':
            dbnamespace = 'js_system'
        else:
            dbnamespace = namespace

        self.dbnamespace = dbnamespace
        self.initall(path, namespace, categoryname)


    def initall(self, path, namespace, categoryname):
        self._init_auth(path, namespace, categoryname)

    def _getObjectId(self, id):
        return pymongo.mongo_client.helpers.bson.objectid.ObjectId(id)

    def incrId(self, counter, size=1):
        seq = counter.find_and_modify({'_id': self.categoryname},
                                      {"$inc": {"seq": size}},
                                      upsert=True)
        if seq:
            return seq['seq'] + size
        else:
            return size

    def runTasklet(self, action, value, session):
        if self.te:
            params = j.core.params.get()
            params.value = value
            params.session = session
            params.action = action
            self.te.execute(params, service=self)

    def setPreSave(self, value, session):
        value = cleankeys(value)
        self.runTasklet('set', value, session)
        return value

    def set(self, key, value, session=None, *args,**kwargs):
        """
        value can be a dict or a raw value (seen as string)
        """
        db, counter = self._getMongoDB(session)
        def idIsZero():
            id = value.get('id')
            if id != None:
                if isinstance(id, int) and id == 0:
                    return True
            return False
        def update(value):
            if isinstance(value['guid'], str):
                value['guid'] = value['guid'].replace('-', '')
        def updateTTL(value):
                if self.TTL != 0:
                    value['_ttl'] = datetime.datetime.utcnow()


        if j.basetype.dictionary.check(value):
            objInDB=None

            obj = self.getObject(value)
            obj.getSetGuid()
            ukey = obj.getUniqueKey()
            value = obj.dump()

            if ukey is not None:
                update(value)
                objInDB=db.find_one({"_id":ukey})
            elif 'guid' in value and value["guid"] != "":
                update(value)
                objInDB=db.find_one({"guid":value["guid"]})

            if objInDB!=None:
                oldckey = self.getObject(objInDB).getContentKey()
                value.pop('id', None)
                value.pop('guid', None)
                objInDB.update(value)
                update(objInDB)
                updateTTL(objInDB)
                objInDB = self.setPreSave(objInDB, session)
                changed = oldckey != self.getObject(objInDB).getContentKey()
                if changed:
                    db.save(objInDB)
                return (objInDB["guid"], False, changed)

            update(value)
            if idIsZero():
                value["id"]=self.incrId(counter)
                obj = self.getObject(value)
                obj.getSetGuid()
                value = obj.dump()
            updateTTL(value)

            value['_id'] = value['guid'] if ukey is None else ukey
            value = self.setPreSave(value, session)

            db.save(value)
            return (value["guid"], True, True)
        else:
            raise RuntimeError("value can only be dict")

    def get(self, key, full=False, session=None):
        self.runTasklet('get', key, session)
        db, counter = self._getMongoDB(session)
        if j.basetype.string.check(key):
            key=key.replace("-","")
            res=db.find_one({"guid":key})
        else:
            res=db.find_one({"guid":key})
            if res is None:
                res=db.find_one({"id":key})

        # res["guid"]=str(res["_id"])
        if not res:
            raise KeyError(key)

        if not full:
            res.pop("_id")
            res.pop("_ttl", None)
        return restorekeys(res)

    def exists(self, key, session=None):
        """
        get dict value
        """
        self.runTasklet('exists', key, session)
        db, counter = self._getMongoDB(session)
        if j.basetype.string.check(key) or isinstance(key, unicode):
            key = key.replace('-', '')
            return not db.find_one({"guid":key})==None
        else:
            return not db.find_one({"id":key})==None

    def index(self, obj,ttl=0,replication="sync",consistency="all",refresh=True):
        #NOT RELEVANT FOR THIS TYPE OF DB
        return

    def delete(self, key, session=None):
        self.runTasklet('delete', key, session)
        db, counter = self._getMongoDB(session)
        try:
            res = self.get(key, True, session=session)
            db.remove(res["_id"])
        except KeyError:
            pass

    def deleteIndex(self, key,waitIndex=False,timeout=1):
        #NOT RELEVANT FOR THIS TYPE OF DB
        pass

    def removeFromIndex(self, key,replication="sync",consistency="all",refresh=True):
        #NOT RELEVANT FOR THIS TYPE OF DB
        pass

    def count(self, query, session=None):
        db, counter = self._getMongoDB(session)
        return db.find(query).count()

    def native(self, methodname, kwargs, session):
        db, counter = self._getMongoDB(session)
        method = getattr(db, methodname)
        kwargs = kwargs or {}
        return method(**kwargs)

    def find(self, query, start=0, size=200, session=None):
        """
        query can be a dict or a string

        when a dict
        @todo describe

        when a string
        query is tag based format with some special keywords

        generic format:  $fieldname:$filter

        special keywords
        - @sort     : comma separated list of fields to sort on
        - @start    : int starting from 0
        - @size     : nr of records to show
        - @fields   : comma separated list of fields to show

        :$filter is
        - absolute value (so the full field)
        - *something*  * is any str
        - time based argument (see below)
        - <10 or >10  (10 is any int)

        example

        'company:acompany creationdate:>-5m nremployees:<4'
        this query would be companies created during last 5 months with less than 4 employees

        special keys for time based search (only relevant for epoch fields):
          only supported now is -3m, -3d and -3h  (ofcourse 3 can be any int)
          and an int which would be just be returned
          means 3 days ago 3 hours ago
          if 0 or '' then is now
          also ok is +3m, ... (+ is for future)
          (is using j.base.time.getEpochAgo & getEpochFuture)



        """
        db, counter = self._getMongoDB(session)
        fields = None
        sorting = None
        if size==None:
            size=200
        sortlist=[]
        if j.basetype.string.check(query):
            tags=j.core.tags.getObject(query)
            sort=None
            if tags.tagExists("@sort"):
                sort=tags.tagGet("@sort")
                tags.tagDelete("@sort")
                for item in sort.split(","):
                    item=item.strip()
                    if item=="":
                        continue
                    if item[0]=="-":
                        item=item.strip("-")
                        sortlist.append((item,-1))
                    else:
                        sortlist.append((item,1))


            if tags.tagExists("@size"):
                size=int(tags.tagGet("@size"))
                tags.tagDelete("@size")

            if tags.tagExists("@start"):
                start=int(tags.tagGet("@start"))
                tags.tagDelete("@start")

            fields=None
            if tags.tagExists("@fields"):
                fields=tags.tagGet("@fields")
                tags.tagDelete("@fields")
                fields=[item.strip() for item in fields.split(",") if item.strip()!=""]

            params=tags.getDict()
            for key, value in list(params.copy().items()):
                if value.startswith('>'):
                    if 'm' in value or 'd' in value or 'h' in value:
                        new_value = j.base.time.getEpochAgo(value[1:])
                    else:
                        new_value = j.basetype.float.fromString(value[1:])
                    params[key] = {'$gte': new_value}
                elif value.startswith('<'):
                    if 'm' in value or 'd' in value or 'h' in value:
                        new_value = j.base.time.getEpochFuture(value[1:])
                    else:
                        new_value = j.basetype.float.fromString(value[1:])
                    params[key] = {'$lte': new_value}
                elif '*' in value:
                    params[key] = {'$regex': '/%s/i' % value.replace('*', ''), '$options': 'i'}

            result=[]
            for item in db.find(params,limit=size,skip=start,fields=fields,sort=sortlist):
                item.pop("_id")
                item.pop("_ttl", None)
                result.append(item)
            return result
        else:
            mongoquery = dict()
            if 'query' in query:
                query.setdefault('query', {'bool':{'must':{}}})
                query['query']['bool'].setdefault('should', {})
                query['query']['bool'].setdefault('must', {})
                for queryitem in query['query']['bool']['must']:
                    if 'term' in queryitem:
                        for k, v in list(queryitem['term'].items()):
                            mongoquery[k] = v
                    if 'range' in queryitem:
                        for k, v in list(queryitem['range'].items()):
                            operatormap = {'from':'$gte', 'to':'$lte', 'gt': '$gt', 'gte': '$gte'}
                            for operator, val in list(v.items()):
                                mongoquery[k] = {operatormap[operator]: val}
                    if 'wildcard' in queryitem:
                        for k, v in list(queryitem['wildcard'].items()):
                            mongoquery[k] = {'$regex': '%s' % str(v).replace('*', ''), '$options':'i'}
                    if 'terms' in queryitem:
                        for k, v in list(queryitem['terms'].items()):
                            mongoquery[k] = {'$in': v}


                mongoquery['$or'] = list()
                for queryitem in query['query']['bool']['should']:
                    wilds = dict()
                    if 'wildcard' in queryitem:
                        for k, v in list(queryitem['wildcard'].items()):
                            wilds[k] = {'$regex': '%s' % str(v).replace('*', ''), '$options': 'i'}
                            mongoquery['$or'].append(wilds)

                if not mongoquery['$or']:
                    mongoquery.pop('$or')
            else:
                fields = query.pop('$fields', None)
                sorting = query.pop('$orderby', None)
                mongoquery = query.pop('$query', None)
                if mongoquery is None:
                    mongoquery = query
            start = int(start)
            size = int(size)
            if 'sort' in query:
                sorting = list()
                for field in query['sort']:
                    sorting.append((list(field.keys())[0], 1 if list(field.values())[0] == 'asc' else -1))
                mongoquery.pop('sort', None)

            if sorting:
                resultdata = db.find(mongoquery, fields=fields).sort(sorting).skip(start).limit(size)
            else:
                resultdata = db.find(mongoquery, fields=fields).skip(start).limit(size)

            count = db.find(mongoquery).count()
            result = [count, ]
            for item in resultdata:
                item.pop("_id")
                item.pop("_ttl", None)
                result.append(item)
            return result

    def aggregate(self, query, session=None):
        db, counter = self._getMongoDB(session)
        return db.aggregate(query)['result']

    def destroyindex(self, session=None):
        db, counter = self._getMongoDB(session)
        db.drop()

    def deleteSearch(self,query, session=None):
        db, _ = self._getMongoDB(session)
        count = db.remove(query)['n']
        return count

    def updateSearch(self, query, update, session=None):
        """
        update is dict or text
        dict e.g. {"name":aname,nr:1}  these fields will be updated then
        text e.g. name:aname nr:1
        """
        if isinstance(query, dict):
            db, _ = self._getMongoDB(session)
            return db.update(query, update, multi=True)
        elif j.basetype.string.check(update):
            tags=j.core.tags.getObject(update)
            update=tags.getDict()
        # self.db.find_and_modify(query,update=update)
        query+=' @fields:guid'
        counter=0
        for item in self.find(query=query, session=session):
            update["guid"]=item["guid"]
            self.set(value=update, session=session)
            counter+=1

        return counter

    def destroy(self, session=None):
        """
        delete objects as well as index (all)
        """
        db, counter = self._getMongoDB(session)
        db.drop()

    def demodata(self, session=None):
        import JumpScale.baselib.redisworker
        path=j.system.fs.joinPaths(self.path,"demodata.py")
        if j.system.fs.exists(path):
            module = imp.load_source("%s_%s_demodata"%(self.namespace,self.categoryname), path)
            job=j.clients.redisworker.execFunction(module.populate,_organization=self.namespace,_category=self.categoryname,_timeout=60,_queue="io",_log=True,_sync=False)

    def list(self, prefix="", withcontent=False, session=None):
        """
        return all object id's stored in DB
        """
        db, counter = self._getMongoDB(session)
        result = list()
        if withcontent:
            cursor = db.find()
            for item in cursor:
                item.pop('_id')
                result.append(item)
        else:
            cursor = db.find(fields=['guid',])
            for item in cursor:
                result.append(item['guid'])
        return result

    def rebuildindex(self, session):
        db, counter = self._getMongoDB(session)
        path=j.system.fs.joinPaths(self.path,"index.py")
        if j.system.fs.exists(path):
            module = imp.load_source("%s_%sindex"%(self.namespace,self.categoryname), path)
            module.index(db)

    def export(self, outputpath,query="", session=None):
        """
        export all objects of a category to json format, optional query
        Placed in outputpath
        """
        if not j.system.fs.isDir(outputpath):
            j.system.fs.createDir(outputpath)
        ids = self.list(session=session)
        for id in ids:
            obj = self.get(id, session=session)
            filename = j.system.fs.joinPaths(outputpath, id)
            if isinstance(obj, dict):
                obj = json.dumps(obj)
            j.system.fs.writeFile(filename, obj)

    def importFromPath(self, path, session=None):
        '''Imports OSIS category from file system'''
        if not j.system.fs.exists(path):
            raise RuntimeError("Can't find the specified path: %s" % path)

        data_files = j.system.fs.listFilesInDir(path)
        for data_file in data_files:
            with open(data_file) as f:
                obj = json.load(f)
            self.set(obj['id'], obj, session=session)
