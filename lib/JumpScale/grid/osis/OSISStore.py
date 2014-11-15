from JumpScale import j
import copy
import imp
import ujson as json
import time

class OSISStore(object):
    """
    Default object implementation (is for one specific namespace_category)
    """

    def __init__(self, dbconnections):
        self.dbconnections = dbconnections
        self.elasticsearch = dbconnections.get("elasticsearch_main")
        self.db = j.db.keyvaluestore.getFileSystemStore("osis")

    def init(self, path, namespace,categoryname):
        """
        gets executed when catgory in osis gets loaded by osiscmds.py (.init method)
        """
        self.initall( path, namespace,categoryname,db=True)

    def initall(self, path, namespace,categoryname,db=False):
        self._init_auth(path, namespace, categoryname, db)
        indexname = self.getIndexName()
        if self.elasticsearch and not self.elasticsearch.indices.exists(indexname):
            self.elasticsearch.indices.create(self.getIndexName())
        self.objectclass=None

    def _init_auth(self, path, namespace, categoryname, db=False):
        self.json=j.db.serializers.getSerializerType("j")

        self.path = path
        self.tasklets = {}

        # for tasklettype in j.system.fs.listDirsInDir(self.path, dirNameOnly=True):
        #     self.tasklets[tasklettype] = j.core.taskletengine.get(j.system.fs.joinPaths(self.path, tasklettype))

        self.namespace = namespace
        self.categoryname = categoryname

        if self.namespace=="" or self.categoryname=="":
            raise RuntimeError("namespace & category cannot be empty")

        self.dbprefix = "%s_%s" % (self.namespace, self.categoryname)
        self.dbprefix_incr = "%s_incr" % (self.dbprefix)

        self.buildlist = False

        authpath=j.system.fs.joinPaths(path,"OSIS_auth.py")
        auth=None
        authparent=None

        if j.system.fs.exists(authpath):
            testmod = imp.load_source("auth_%s"%self.dbprefix, authpath)
            auth=testmod.AUTH()
            auth.load(self)

        authpath=j.system.fs.joinPaths(j.system.fs.getParent(path),"OSIS_auth.py")
        if j.system.fs.exists(authpath):
            testmod = imp.load_source("auth_%s"%self.dbprefix, authpath)
            authparent=testmod.AUTH()
            authparent.load(self)

        self.auth=auth
        if self.auth==None and authparent<>None:
            self.auth=authparent

    def get(self, key, session=None):
        """
        get dict value
        """
        return self.db.get(self.dbprefix, key)

    def exists(self, key, session=None):
        """
        get dict value
        """
        return self.db.exists(self.dbprefix, key)

    def checkChangeLog(self):
        if self.db<>None:
            self.db.checkChangeLog()

    def getObject(self, ddict={}):
        klass=j.core.osis.getOsisModelClass(self.namespace,self.categoryname)
        if klass=="":
            return ddict            
        obj = klass(ddict=ddict)
        return obj

    def setObjIds(self,obj):
        """
        for osis object get unique id & set it in object
        return (new,changed,obj) #new & changed=boolean
        """        
        ckey=obj.getContentKey()
        # print "ckey:%s"%ckey
        ukey=obj.getUniqueKey()
        # print "ukey:%s"%ukey
        if ukey==None or str(ukey)=="":
            # print "UKEY NONE SO NEW"
            changed=True
            new=True
            ukey=None
        else:
            changed=False
            new=False
        
        if ukey<>None and self.db.exists(self.dbprefix_incr, ukey):
            # print "ukey exists"
            new=False            
            id,guid,ckey2=self.json.loads(self.db.get(self.dbprefix_incr, ukey))
            guid=str(guid)
            ckey=str(ckey)
            ckey2=str(ckey2)
            # print "guid,ckey in db: %s:%s"%(guid,ckey2)
            if obj.id<>id:
                obj.id=id
            obj.getSetGuid()
            if obj.guid<>guid:
                # print "GUID changed"
                changed=True
            ckey=obj.getContentKey()
            if ckey2<>ckey:
                # print "content changed"
                changed=True
            if changed:
                json=self.json.dumps([obj.id,obj.guid,ckey])
                self.db.set(self.dbprefix_incr, ukey, json)       
            # print "ret:%s %s" %(new,changed)         
            return (new,changed,obj)
        else:
            # print "ukey not in db"
            new=True
            changed=True    
            if not hasattr(obj, 'id') or not obj.id:
                id=self.db.increment(self.dbprefix_incr)
                # print "newid:%s"%id
                obj.id=id
            obj.getSetGuid()
            ukey=obj.getUniqueKey()
            ckey=obj.getContentKey()
            obj._ckey=ckey
            # print "ukey,ckey for new object: %s:%s"%(ukey,ckey)
            if ukey<>None:
                json=self.json.dumps([obj.id,obj.guid,ckey])
                self.db.set(self.dbprefix_incr, ukey, json)
            return (new,changed,obj)

    def set(self, key, value,waitIndex=False, session=None):
        """
        value can be a dict or a raw value (seen as string)
        if raw value then will not try to index
        """
        if j.basetype.dictionary.check(value):
            #is probably an osis object
            obj=self.getObject(value)
            if not j.basetype.dictionary.check(obj):
                new,changed,obj=self.setObjIds(obj)
                key=obj.guid
                if changed:                  
                    self.index(obj)
                    value2=self.json.dumps(obj.obj2dict())
                    if waitIndex:
                        time.sleep(0.2)
                        if not self.existsIndex(key=obj.guid,timeout=1):
                            raise RuntimeError("index not stored for key:%s in %s:%s"(key,self.namespace, self.categoryname))
            else:
                if key==None:
                    if value.has_key("guid"):
                        key=value["guid"]
                    else:
                        raise RuntimeError("could not find guid attr on obj for %s:%s"(self.namespace, self.categoryname))                
                else:
                    if not value.has_key("guid"):
                        value["guid"]=key
                value2=self.json.dumps(value)
                self.db.set(self.dbprefix, key=key, value=value2)                
                self.index(value)
                if waitIndex:
                    time.sleep(0.2)
                    if not self.existsIndex(key=obj.guid,timeout=1):
                        raise RuntimeError("index not stored for key:%s in %s:%s"(key,self.namespace, self.categoryname))               
                new=None
                changed=None
        else:
            new=True
            changed=True
            raise RuntimeError("val should be dict or osisobj")

        if changed:
            self.db.set(self.dbprefix, key=key, value=value2)
        return (key,new,changed)

    def getIndexName(self):
        """
        return name of index in elastic search, depends on properies of object
        """
        return self.dbprefix

    def index(self, obj,ttl=0,replication="sync",consistency="all",refresh=True):
        """
        @param ttl = time to live in seconds of the index
        """
        if self.elasticsearch == None:
            return

        index = self.getIndexName()

        if j.basetype.dictionary.check(obj):
            data=copy.copy(obj)
            data=obj
        else:
            if hasattr(obj,"getDictForIndex"):
                data=obj.getDictForIndex()
            else:
                if isinstance(obj, basestring):
                    obj = self.json.loads(obj)
                    data=copy.copy(obj)
                else:
                    data=copy.copy(obj.__dict__)

        guid=data["guid"]

        # data.pop("guid")  # remove guid from object before serializing to json
        for key5 in data.keys():
            if key5[0] == "_":
                data.pop(key5)
        try:
            data.pop("sguid")
        except:
            pass       
        
        try:
            if ttl <> 0:
                self.elasticsearch.index(index=index, id=guid, doc_type="json", doc=data, ttl=ttl, replication=replication,consistency=consistency,refresh=refresh,overwrite_existing=True)
            else:
                self.elasticsearch.index(index=index, id=guid, doc_type="json", doc=data, replication=replication,consistency=consistency,refresh=refresh,overwrite_existing=True)
        except Exception,e:

            if str(e).find("Index failed")<>-1:
                try:
                    msg="cannot index object:\n%s"%data
                except Exception,ee:
                    msg="cannot index object, cannot even print object"                
                print e
                j.errorconditionhandler.raiseOperationalCritical(msg, category='osis.index', msgpub='', die=False, tags='', eco=None)
            elif str(e).find("failed to parse")<>-1:
                try:
                    msg="indexer cannot parse object (normally means 1 or more subtypes of doc was changed)"
                except Exception,ee:
                    msg="indexer cannot parse object, cannot even print object.\n%s"%ee
                    j.errorconditionhandler.raiseOperationalCritical(msg, category='osis.index.parse', msgpub='', die=False, tags='', eco=None)
                    return
                j.errorconditionhandler.raiseOperationalCritical(msg, category='osis.index.parse', msgpub='', die=False, tags='', eco=None,extra=data)
            else:
                eco=j.errorconditionhandler.parsePythonErrorObject(e)
                eco.process()

    def existsIndex(self,key,timeout=0):
        if key==None:
            raise RuntimeError("key cannot be None")
        q = {'query': {'bool': {'must': [{'term': {'guid': key}}]}}}
        ok=False
        if timeout>0:
            now=time.time()
            end=now+timeout            
            while now<end:
                res=self.find(q)
                if res["total"]>0:
                    ok=True
                    break
                time.sleep(0.1)
                # print "index not ready yet"
        else:
            res=self.find(q)
            if res["total"]>0:
                ok=True
        return ok

    def delete(self, key, session=None):
        self.db.delete(self.dbprefix, key)
        self.removeFromIndex(key)

    def deleteIndex(self, key,waitIndex=False,timeout=1, session=None):
        self.removeFromIndex(key)
        if waitIndex and timeout>0:
            now=time.time()
            end=now+timeout            
            while now<end:
                if not self.existsIndex(key):
                    return
                time.sleep(0.1)
                # print "index not ready yet for delete"
            raise RuntimeError("Could not delete index in time for key:%s"%key)

    def removeFromIndex(self, key,replication="sync",consistency="all",refresh=True):
        index = self.getIndexName()
        try:
            result = self.elasticsearch.delete(index, 'json', key, replication=replication,consistency=consistency,refresh=refresh)
        except Exception,e:
            j.errorconditionhandler.processPythonExceptionObject(e)
            result=None
        return result

    def find(self, query, start=0, size=None, session=None):
    
        if not isinstance(query, dict):
            query = self.json.loads(query)
        
        index = self.getIndexName()
        size = size or 100000

        try:
            result = self.elasticsearch.search(query=query, index=index, es_from=start,
                                           size=size)
        except:
            result = {'hits': {'hits': list(), 'total': 0}}
        if not isinstance(result, dict):
            result = result()
        return {'result': result['hits']['hits'],
                'total': result['hits']['total']}

    def destroyindex(self):
        if len(self.categoryname) < 4:
            j.errorconditionhandler.raiseBug(message="osis categoryname needs to be at least 3 chars.", category="osis.bug")
        indexes = self.elasticsearch.get_mapping().keys()
        for i in indexes:
            if i.find(self.dbprefix) == 0:
                self.elasticsearch.delete_index(i)

    def destroy(self, session=None):
        """
        delete objects as well as index (all)
        """
        self.destroyindex()
        
        self.db.destroy(category=self.dbprefix)
        self.db.destroy(category=self.dbprefix_incr)
        self.db.incrementReset(self.dbprefix_incr)

    def list(self, prefix="", withcontent=False, session=None):
        """
        return all object id's stored in DB
        """
        db = self.db
        if withcontent == False:
            return db.list(self.dbprefix, prefix)

    def rebuildindex(self):
        #@todo push to worker, this will be too slow (best to create sort of mapreduce alike technique)
        self.destroyindex()
        ids = self.list()
        for id in ids:
            obj = self.get(id)
            self.index(obj)

    def export(self, outputpath, session=None):
        """
        export all objects of a category to json format.
        Placed in outputpath
        """
        if not j.system.fs.isDir(outputpath):
            j.system.fs.createDir(outputpath)
        ids = self.list()
        for id in ids:
            obj = self.get(id)
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
            self.set(obj['guid'], obj)
