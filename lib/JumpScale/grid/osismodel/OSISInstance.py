from JumpScale import j
# from IndexerWhoosh import IndexerWhoosh


class OSISInstanceNoDB(object):

    def __init__(self, appname, actorname, modelname, classs):
        self.modelclass = classs
        self.appname = appname
        self.actorname = actorname
        self.modelname = modelname
        self.spec = j.core.specparser.getModelSpec(self.appname, self.actorname, self.modelname)
        idspec = [item for item in self.spec.properties if item.name == "id"]
        if len(idspec) > 0:
            idspec = idspec[0]
            self.idType = idspec.type
        else:
            self.idType = None

        self.listProps = ["id", "guid"]
        for propspec in self.spec.properties:
            tags = j.core.tags.getObject(propspec.tags)
            if tags.labelExists("list"):
                if propspec.name not in self.listProps:
                    self.listProps.append(propspec.name)

    def _getObj(self, obj):
        if isinstance(obj, dict):
            attributes = obj.copy()
            return j.code.dict2JSModelobject(self.modelclass(), attributes)
        else:
            return obj

    def _getDict(self, obj):
        if isinstance(obj, dict):
            return obj
        elif isinstance(obj, self.modelclass):
            return obj.obj2dict()

    def new(self):
        """
        Create new object from class & return
        """
        obj = self.modelclass()
        obj.guid = j.base.idgenerator.generateGUID()
        return obj


class OSISRemoteOSISInstance(OSISInstanceNoDB):

    def __init__(self, appname, actorname, modelname, classs):
        OSISInstanceNoDB.__init__(self, appname, actorname, modelname, classs)
        self.remoteOSISClient = j.core.osis.getClientByInstance('main')

    def _getObj(self, obj):
        obj = self._getDict(obj)
        return j.core.grid.zobjects.getModelObject(obj)

    def set(self, obj):
        value = self._getObj(obj)
        id = getattr(value, 'id', None)
        key, new, changed = self.remoteOSISClient.set(self.actorname, self.modelname, id, value.getSerializable())
        return key

    def get(self, guid=None, id=None):
        # TODO invoke guid to id osis call
        obj = self.remoteOSISClient.get(self.actorname, self.modelname, id)
        return j.code.dict2JSModelobject(self.modelclass(), obj)

    def delete(self, guid=None, id=None):
        # TODO invoke guid to id osis call
        self.remoteOSISClient.delete(self.actorname, self.modelname, id)
        return

    def find(self, query, start=0, size=None):
        return self.remoteOSISClient.search(self.actorname, self.modelname, query, start, size)

    def list(self, prefix=None):
        return self.remoteOSISClient.list(self.actorname, self.modelname, prefix)


class OSISInstance(OSISInstanceNoDB):

    """
    """

    def __init__(self, appname, actorname, modelname, classs, db, index=False, indexer=None):
        OSISInstanceNoDB.__init__(self, appname, actorname, modelname, classs)
        self._db = db
        if index:
            self.indexer = indexer
            # if indexer==None:
            #     self.indexer=IndexerWhoosh("%s_%s_%s" % (appname,actorname,modelname))
            # else:
            #     self.indexer=indexer
        else:
            self.indexer = None

        self.lastNrRecords = self.getNrRecords()

    def new(self, guid=None, id=None):
        """
        Create new object, generate id if needed, do not store !!!
        """
        obj = self.modelclass()
        if guid == None:
            obj.guid = j.base.idgenerator.generateGUID()
        else:
            obj.guid = guid
        if id != None:
            obj.id = id
        elif self.idType == "int":
            obj.id = self._db.increment("%s__%s" % (self.actorname, self.modelname))
        return obj

    def getNrRecords(self):
        return self._db.getNrRecords(self.modelname)

    def link(self, obj):
        self._db.set("modeli_%s" % self.modelname, "%s" % obj.guid, str(obj.id))

    def set(self, obj, index=False):
        data = self._getDict(obj)
        if 'guid' not in data or not data['guid']:
            data['guid'] = j.base.idgenerator.generateGUID()

        if self.exists(id=data['id']):
            saveddata = self.get(id=data['id']).obj2dict()
            saveddata.update(data)
        else:
            saveddata = data
        self._db.delete("modellist", self.modelname)
        self._db.set("model_%s" % self.modelname, saveddata['id'], saveddata)
        obj = self._getObj(saveddata)
        self.link(obj)
        self.getNrRecords()
        if index:
            self._index(obj)
        return obj.id

    def _index(self, obj):
        if self.indexer != None:
            spec = j.core.specparser.getModelSpec(self.appname, self.actorname, self.modelname)
            indexcontent = self.indexer.indexdef.getIndexArgs(obj, j.core.osis.objectToText4Index(obj, spec))
            self.indexer.addIndexContent(indexcontent)

    def _getId(self, guid, id, ignoreError=False):
        if not id:
            id = self.getguid2id(id, guid, ignoreError=ignoreError)
        return id

    def get(self, guid=None, id=None, createIfNeeded=False, ignoreError=False):
        key = "model_%s" % self.modelname
        if createIfNeeded and not self.exists(guid, id):
            # did not find object, will create
            obj = self.new(guid, id)
            self.set(obj)
            print("get object did not exist:%s %s %s " % (self.modelname, guid, id))
            return obj

        id = self._getId(guid, id)
        value = self._db.get(key, str(id))
        return j.code.dict2JSModelobject(self.modelclass(), value)

    def getguid2id(self, id=None, guid=None, ignoreError=False):
        """
        @param guidCheck, if used will check that the guid returned is same as referenced by id
        """
        if self._db.exists("modeli_%s" % self.modelname, str(guid)):
            dbid = self._db.get("modeli_%s" % self.modelname, str(guid))
            if id and dbid != id:
                if ignoreError == False:
                    raise RuntimeError("Found an object (type:%s) starting from guid:%s which had already id assigned which is different than the one asked for.\nAsked:%s, found:%s"
                                       % (self.modelname, guid, id, dbid))
            return dbid
        if ignoreError:
            return None
        raise RuntimeError("Cannot find object %s with id %s" % (self.modelname, guid))

    def exists(self, guid=None, id=None):
        if not id:
            guid = self.getguid2id(id, guid, ignoreError=True)
            if guid != None:
                exist = self._db.exists("model_%s" % self.modelname, str(id))
                if exist:
                    return True
                else:
                    # corruption in db, remove the reference
                    self._db.delete("modeli_%s" % self.modelname, str(guid))
                    return False
            else:
                return False
        else:
            return self._db.exists("model_%s" % self.modelname, str(id))

    def delete(self, guid=None, id=None):
        # delete metadata about model in cat modellist
        self._db.delete("modellist", self.modelname)
        id = self._getId(guid, id)
        if self.indexer != None:
            self.indexer.delete(id)
        if self._db.exists("model_%s" % self.modelname, str(id)):
            # now starting from object remove the id which also refers to this obj
            obj = self.get(id=id)
            if self._db.exists("modeli_%s" % self.modelname, str(obj.guid)):
                self._db.delete("modeli_%s" % self.modelname, str(obj.guid))
            self._db.delete("model_%s" % self.modelname, str(id))

    def optimize(self):
        if self.indexer != None:
            self.indexer.optimize()

    def find(self, query, start=0, size=None):
        if self.indexer != None:
            return self.indexer.find(query, start, size)
        else:
            raise RuntimeError("Cannot find indexer")

    def destroyindex(self):
        if self.indexer != None:
            self.indexer.destroy()

    def destroy(self):
        """
        delete objects as well as index (all)
        """
        self.destroyindex()
        try:
            return self._db.destroy()
        except:
            pass
        ids = self.list()
        for id in ids:
            self.delete(id)
        self._db.incrementReset(self.modelname)
        self._db.delete("modellist", self.modelname)
        # kkey="%s_%s_%s" % (self.appname,self.actorname,self.modelname)
        # if j.core.osis.osisInstances.has_key(kkey):
        #     j.core.osis.osisInstances.pop(kkey)

    def obj2ini(self, fields=[], section="main"):
        """
        convert osis object to an inifile, only properties of root are used
        """

    # def ini2objects(self, cfgpath, overwriteInDB=True, deepcheck=True, ignoreWhenNotExist=False, manipulator=None,
    #                 manipulatorargs={}, limitVars=[], writeIni=True):
    #     """
    #     read inifile
    #     each section is a new object
    #     see if obj exists (starting from id & guid)
    #     when overwriteInDB=True
    #       if obj found overwrite values in db from cfg file
    #     else:
    #       overwrite the ini file
    #     when deepcheck then check against inconsistencies
    #     @param ignoreWhenNotExist if true will continue even if ini file does not exists

    #     manipulator method allows you to manipulate ini file & obj, if changes will be saved on disk or in db
    #     ini2,objFromDb,objFromIni,skip=manipulator(ini,section,existsInDb,objFromDB,objFromIni)
    #       existsInDb is True when it did exist in db
    #         when method puts skip on True then ini2object will return False

    #     """
    #     result = []
    #     if j.system.fs.exists(cfgpath):
    #         ini = j.tools.inifile.open(cfgpath)
    #         for name in ini.getSections():
    #             if ini.checkParam(name, "create"):
    #                 create = ini.getIntValue(name, "create") == 1
    #             else:
    #                 create = True
    #             # create true means we will overwrite the db
    #             obj = self.ini2object(cfgpath, section=name, overwriteInDB=create, manipulator=manipulator, manipulatorargs=manipulatorargs,
    #                                   limitVars=limitVars, writeIni=writeIni)
    #             if obj != None:
    #                 result.append(obj)
    #         return result
    #     else:
    #         if ignoreWhenNotExist:
    #             return []
    #         raise RuntimeError("Cannot find ini %s to convert to objects" % cfgpath)

    # def ini2object(self, cfgpath, section="main", overwriteInDB=True, manipulator=None, manipulatorargs={}, limitVars=[], writeIni=True):
    #     """
    #     read inifile
    #     see if obj exists (starting from id & guid)
    #     when overwriteInDB=True
    #       if obj found overwrite values in db from cfg file
    #     else:
    #       overwrite the ini file
    #     when deepcheck then check against inconsistencies
    #     if useId: then will use id when specified in inifile, if false will remove



    #     """
    #     print "ini2object for cfgpath:%s and section:%s" % (cfgpath, section)

    #     if j.system.fs.exists(cfgpath):
    #         ini = j.tools.inifile.open(cfgpath)
    #     else:
    #         ini = j.tools.inifile.new(cfgpath)
    #     if section != "main":
    #         id = section
    #     else:
    #         if ini.checkParam(section, "id"):
    #             id = str(ini.getValue(section, "id"))
    #         else:
    #             id = None

    #     guid = None
    #     if ini.checkParam(section, "guid"):
    #         guid = str(ini.getValue(section, "guid"))
    #         if guid.strip() == "":
    #             guid = None

    #     ini.setParam(section, "id", id)
    #     if section == "main" and not ini.checkParam(section, "id") and id != None:
    #         ini.write()

    #     if ini.checkParam(section, "reset"):
    #         # if there is a reset value the overwriteindb will be adjusted following the reset value
    #         overwriteInDB = str(ini.getValue(section, "reset")) == "1"

    #     existsInDb = self.exists(guid=guid, id=id)
    #     if not existsInDb:
    #         overwriteInDB = True

    #     obj = self.get(guid, id, createIfNeeded=True, ignoreError=True)

    #     if obj.guid != guid and guid != None:
    #         # found object but guid is not correct
    #         if overwriteInDB:
    #             obj.guid = guid
    #             self.set(obj)
    #         else:
    #             guid = obj.guid
    #             # will no longer remember guid on config files
    #             # ini.setParam(section,"guid",guid)
    #             # ini.write()

    #     elif guid == None:
    #         guid = obj.guid

    #     if obj == None and self.exists(guid):
    #         # found object
    #         obj = self.get(guid)
    #         self.link(obj)

    #     objnew = self.new()  # is only in mem, does not get stored in DB

    #     def check2process(name):
    #         if name in ["create", "reset"]:
    #             return False
    #         if limitVars != [] and name not in limitVars:
    #             return False
    #         return True

    #     params = []
    #     spec = self.spec
    #     for prop in spec.properties:
    #         # print "check2process:%s %s"%(prop.name,check2process(prop.name))
    #         value = None
    #         if check2process(prop.name):
    #             # print "section:%s propname:%s" %(section,prop.name)
    #             default = prop.default
    #             ttype = prop.type
    #             name = prop.name
    #             params.append(name)
    #             if name != "id" or section == "main":
    #                 if not ini.checkParam(section, name):
    #                     ini.setParam(section, name, "")
    #                     if writeIni:
    #                         ini.write()
    #                 if ttype == "int":
    #                     value = ini.getValue(section, name)
    #                     if value == "" or value.lower() == "none":
    #                         value = 0
    #                         ini.setParam(section, name, 0)
    #                         if writeIni:
    #                             ini.write()
    #                     else:
    #                         value = int(value)
    #                     if value == 0 and str(default) != "":
    #                         value = int(default)
    #                 elif ttype == "str":
    #                     value = str(ini.getValue(section, name))
    #                     if not value and str(default):
    #                         value = str(default)
    #                 elif ttype == "bool":
    #                     value = str(ini.getValue(section, name))
    #                     if value == "1":
    #                         value = True
    #                     else:
    #                         value = False
    #                 elif ttype == "list(str)":
    #                     value = [item.strip() for item in str(ini.getValue(section, name)).split(",")]
    #                 elif ttype == "list(int)":
    #                     value = [int(item) for item in str(ini.getValue(section, name)).split(",")]
    #             else:
    #                 if name == "id":
    #                     key = "_P_%s" % prop.name
    #                     objnew.__dict__[key] = id

    #             key = "_P_%s" % prop.name
    #             # print "objnew: %s %s" %(prop.name,value)
    #             if prop.name == "guid" and value == "":
    #                 continue
    #             if value != None:
    #                 objnew.__dict__[key] = value

    #     if manipulator != None:
    #         ini2, obj, objnew, skip = manipulator(ini, section, existsInDb, obj, objnew, manipulatorargs)
    #         if ini2 != ini and ini2 != None:
    #             ini.write()

    #         if skip:
    #             return None

    #     if obj == None:
    #         obj = objnew
    #         obj.guid = j.base.idgenerator.generateGUID()
    #         self.link(obj)
    #         self.set(obj)
    #         ini.setParam(section, "guid", obj.guid)
    #         if writeIni:
    #             ini.write()
    #     else:
    #         # will compare if objects are alike
    #         if not self.checkEqualNoId(obj, objnew):
    #             # oeps objects are not alike
    #             if overwriteInDB:
    #                 self.set(objnew)
    #                 obj = objnew
    #             else:
    #                 self.set(obj)

    #     return obj

    def checkEqualNoId(self, obj1, obj2):
        """
        convert obj1 & 2 to dict and remove id & guid
        check if all other fields are equal
        """
        def normalize(obj):
            d = obj.obj2dict()
            if "id" in d:
                d.pop("id")
            if "guid" in d:
                d.pop("guid")
            return str(d).replace(" ", "").strip()

        return normalize(obj1) == normalize(obj2)

    def list(self, withcontent=False):
        """
        return all object id's stored in DB
        """
        db = self._db
        cat = "model_%s" % self.modelname
        # if self.lastNrRecords==0:
        #     return []
        # if cat not in db.listCategories():

        if withcontent == False:
            return db.list(cat, "")

        if self._db.exists("modellist", self.modelname):
            r = self._db.get("modellist", self.modelname)
            return r

        result = []
        for item in db.list(cat, ""):
            ob = self.get(id=item)
            row = []
            for prop in self.listProps:
                r = ob.__dict__["_P_%s" % prop]
                if j.basetype.list.check(r):
                    r = ",".join(r)
                if j.basetype.dictionary.check(r):
                    for key in list(r.keys()):
                        r += "%s:%s," % (key, r[key])
                    r.rstrip(",")
                row.append(r)
            result.append(row)
        self._db.set("modellist", self.modelname, result)
        return result

    def rebuildindex(self):
        self.destroyindex()
        ids = self.list()
        for id in ids:
            obj = self.get(id=id)
            self._index(obj)
