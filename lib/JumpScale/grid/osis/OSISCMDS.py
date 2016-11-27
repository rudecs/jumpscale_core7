from JumpScale import j
import gevent
import time


class OSISCMDS(object):
    dbconnections = None

    def __init__(self, daemon):
        self.daemon = daemon
        self.osisInstances = {}  # key is namespace_categoryname
        self.db = None  # default db
        self.path = "%s/apps/osis/logic" % j.dirs.baseDir

    def authenticate(self, namespace, categoryname, name, passwd, session=None):
        """
        authenticates a user and returns the groups in which the user is
        """
        if namespace == "system" and categoryname == "node":
            oi = self._getOsisInstanceForCat("system", "node")
            return oi.auth.authenticate(oi, 'auth', name, passwd, session)

        if namespace != "system" or categoryname != "user":
            raise RuntimeError("Cannot process, only supported for system/user namespace")
        oi = self._getOsisInstanceForCat("system", "user")

        query = {'id': name, 'active': True}
        results = oi.find(query, session=session)[1:]
        if not results:
            return {"authenticated": False, "exists": False}

        userguid = results[0]['guid']
        user = oi.get(userguid, session=session)

        if user["passwd"] == j.tools.hash.md5_string(passwd):
            return {"authenticated": True, "exists": True, "groups": user["groups"],
                    "passwdhash": user["passwd"], "authkey": user["authkey"]}

        return {"authenticated": False, "exists": True}

    def _doAuth(self, namespace, categoryname, session):
        oi = self._getOsisInstanceForCat(namespace, categoryname)
        if hasattr(oi, 'auth') and oi.auth != None:
            if oi.auth.authenticate(oi, "get", session.user, session.passwd, session=session) == False:
                raise RuntimeError("Authentication error on get %s_%s for user %s" %
                                   (namespace, categoryname, session.user))
        return oi

    def get(self, namespace, categoryname, key, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.get(key, session=session)

    def exists(self, namespace, categoryname, key, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.exists(key, session)

    def existsIndex(self, namespace, categoryname, key, timeout=1, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.existsIndex(key, timeout=timeout, session=session)

    def set(self, namespace, categoryname, key=None, value=None, waitIndex=False, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.set(key=key, value=value, waitIndex=waitIndex, session=session)

    def delete(self, namespace, categoryname, key, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.delete(key=key, session=session)

    def destroy(self, namespace, categoryname, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.destroy(session)

    def demodata(self, namespace, categoryname, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.demodata(session)

    def search(self, namespace, categoryname, query, start=0, size=None, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        result = oi.find(query, start, size, session)
        return result

    def aggregate(self, namespace, categoryname, query, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        result = oi.aggregate(query, session)
        return result

    def deleteSearch(self, namespace, categoryname, query, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.deleteSearch(query=query, session=session)

    def updateSearch(self, namespace, categoryname, query, update, session=None):
        """
        update is dict or text
        dict e.g. {"name":aname,nr:1}  these fields will be updated then
        text e.g. name:aname nr:1
        """
        oi = self._doAuth(namespace, categoryname, session)
        return oi.updateSearch(query=query, update=update, session=session)

    def list(self, namespace, categoryname, prefix=None, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        if prefix == None:
            return oi.list(session=session)
        return oi.list(prefix, session=session)

    def count(self, namespace, categoryname, query=None, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.count(query, session=session)

    def native(self, namespace, categoryname, methodname, kwargs=None, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.native(methodname=methodname, session=session, kwargs=kwargs)

    def checkChangeLog(self):
        rediscl = None
        if not j.application.config.exists("rediskvs.master.addr"):
            return
        while True:
            if j.system.net.tcpPortConnectionTest('127.0.0.1', port=7771):
                try:
                    if rediscl == None:
                        rediscl = j.db.keyvaluestore.getRedisStore(namespace='', host='127.0.0.1', port=7771)
                    rediscl.checkChangeLog()
                except Exception as e:
                    j.errorconditionhandler.processPythonExceptionObject(e)
            yield gen.Task(self.loop.add_timeout, time.time() + 2)
            # gevent.sleep(2)

    def _rebuildindex(self, namespace, categoryname, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.rebuildindex(session)

    def rebuildindex(self, namespace=None, categoryname=None, session=None):
        if not namespace and not categoryname:
            for ns in self.listNamespaces():
                for cat in self.listNamespaceCategories(ns):
                    try:
                        self._rebuildindex(ns, cat, session)
                    except Exception as e:
                        j.errorconditionhandler.raiseOperationalWarning(
                            "Did not rebuild index for category '%s' in namespace '%s'. Error was: %s" % (cat, ns, e))
        else:
            self._rebuildindex(namespace, categoryname, session)

    def export(self, namespace, categoryname, outputpath, session=None, **kwargs):
        oi = self._doAuth(namespace, categoryname, session=session)
        return oi.export(outputpath, session=session)

    def importFromPath(self, namespace, categoryname, path, session=None):
        oi = self._doAuth(namespace, categoryname, session)
        return oi.importFromPath(path, session)

    def echo(self, msg="", session=None):
        return msg

    def getStatus(self, session=None):
        status = dict()
        for conntype, conn in list(self.dbconnections.items()):
            if conntype.startswith('mongodb'):
                status['mongodb'] = conn.alive()
            elif conntype.startswith('influxdb'):
                try:
                    conn.get_list_database()
                    status['influxdb'] = True
                except Exception:
                    status['influxdb'] = False
        return status

    # 3

    def _getOsisInstanceForCat(self, namespace, category):
        fullname = "%s_%s" % (namespace, category)
        if fullname in self.osisInstances:
            return self.osisInstances[fullname]

        j.errorconditionhandler.raiseBug(
            message="cannot find osis local instance for namespace:%s & category:%s" % (namespace, category), die=False,
            category="osis.valueerror")

    def _authenticateAdmin(self, session=None, user=None, passwd=None, die=True):
        if session != None:
            user = session.user
            passwd = session.passwd

        if user == "root":
            if j.core.osis.superadminpasswd is None:
                j.application.loadConfig()
                j.core.osis.superadminpasswd = j.application.config.get("osis.superadmin.passwd")
                if j.core.osis.superadminpasswd == "":
                    raise RuntimeError("osis.superadmin.passwd cannot be empty in hrd")

            if passwd == j.core.osis.superadminpasswd:
                return True
            if j.tools.hash.md5_string(passwd) == j.core.osis.superadminpasswd:
                return True
        else:
            if die:
                raise RuntimeError("Could not authenticate for admin usage, user login was %s" % user)
            else:
                return False

    def createNamespace(self, name=None, incrementName=False, template=None, session=None):
        """
        @return True
        """
        if session != None:
            self._authenticateAdmin(session)
        # deal with incrementName
        if name == None:
            name = str()
        if incrementName:
            name += str(self._incrementNamespaceId())

        if j.system.fs.exists(j.system.fs.joinPaths(self.path, name)):
            # check namespace exists, if yes just return True
            return True

        # namespace does not exist yet
        j.system.fs.createDir(j.system.fs.joinPaths(self.path, name))
        if template != None:
            j.system.fs.copyDirTree(j.system.fs.joinPaths(self.path, "_%s" % template),
                                    j.system.fs.joinPaths(self.path, name), overwriteFiles=False)

        path = j.system.fs.joinPaths(self.path, name)

        self._initDefaultContent(namespacename=name)
        self.init(path=self.path, namespacename=name, template=template)
        return True

    def getOsisObjectClassCodeOrSpec(self, namespace, categoryname, session=None):
        """
        @return (1,spec file for osis complex time)
        @return (2,content of model.py)
        @return (3,"")  #could not find
        """

        path = j.system.fs.joinPaths(self.path, namespace, categoryname, "model.py")
        genclassname = "%s_%s_osismodelbase" % (namespace, categoryname)
        osismodelpath = j.system.fs.joinPaths(self.path, namespace, categoryname, "%s.py" % (genclassname))
        if j.system.fs.exists(path):
            model = j.system.fs.fileGetContents(path)
            if j.system.fs.exists(osismodelpath):
                model = j.system.fs.fileGetContents(osismodelpath) + model
                model = model.replace("from %s import %s" % (genclassname, genclassname), "")
            return 2, model
        else:
            return 3, ""

    def getOsisSpecModel(self, namespace, session=None):
        result = {}
        for ttype in j.core.specparser.getModelNames("osismodel", namespace):
            obj = j.core.specparser.getModelSpec("osismodel", namespace, ttype)
            result[ttype] = obj.obj2dict()
        return result

    def listNamespaces(self, prefix="", session=None):
        ddirs = j.system.fs.listDirsInDir(self.path, dirNameOnly=True)

        ddirs = [item for item in ddirs if not item.find("_") == 0]

        if prefix != "":
            ddirs = [item for item in ddirs if item.find(prefix) == 0]

        return ddirs

    def listNamespaceCategories(self, namespacename, session=None):
        ddirs = j.system.fs.listDirsInDir(j.system.fs.joinPaths(self.path,
                                                                namespacename), dirNameOnly=True)
        return ddirs

    def deleteNamespaceCategory(self, namespacename, name, removecode=False, session=None):
        """
        """
        if session != None:
            self._authenticateAdmin(session)
        namespacepath = j.system.fs.joinPaths(self.path, namespacename)
        if not j.system.fs.exists(path=namespacepath):
            raise RuntimeError("Could not find namespace with name:%s" % namespacename)
        if removecode:
            j.system.fs.removeDirTree(j.system.fs.joinPaths(namespacepath, name))
        key = "%s_%s" % (namespacename, name)
        try:
            self.elasticsearch.delete_index(key)
        except:
            pass
        self.db.destroy(key)
        self.db.destroy(key + "_incr")

    def createNamespaceCategory(self, namespacename, name, session=None):
        """
        """
        if session != None:
            self._authenticateAdmin(session)
        namespacepath = j.system.fs.joinPaths(self.path, namespacename)
        if not j.system.fs.exists(path=namespacepath):
            raise RuntimeError("Could not find namespace with name:%s" % namespacename)

        j.system.fs.createDir(j.system.fs.joinPaths(namespacepath, name))

        self.init(path=self.path, overwriteImplementation=False, namespacename=namespacename)

    def _initDefaultContent(self,  namespacename=None):
        path = self.path
        if namespacename == None:
            for namespacename in j.system.fs.listDirsInDir(path, dirNameOnly=True):
                self._initDefaultContent(namespacename=namespacename)
        else:
            templatespath = "_templates"
            if j.system.fs.exists(path=templatespath):

                # if j.system.fs.exists(path):
                templatespath_namespace = j.system.fs.joinPaths(templatespath, "namespace")
                templatespath_category = j.system.fs.joinPaths(templatespath, "category")
                namespacepath = j.system.fs.joinPaths(path, namespacename)
                j.system.fs.copyDirTree(templatespath_namespace, namespacepath, overwriteFiles=False)
                if namespacename[0] != "_" and j.system.fs.exists(path=j.system.fs.joinPaths(namespacepath, ".parentInTemplate")):
                    # check if parent is coming from template
                    j.system.fs.remove(j.system.fs.joinPaths(namespacepath, "OSIS_parent.py"))
                    j.system.fs.remove(j.system.fs.joinPaths(namespacepath, "OSIS_parent.pyc"))

                for catname in j.system.fs.listDirsInDir(namespacepath, dirNameOnly=True):
                    catpath = j.system.fs.joinPaths(namespacepath, catname)
                    j.system.fs.copyDirTree(templatespath_category, catpath, overwriteFiles=False)
                    # j.system.fs.copyDirTree(templatespath_osistasklets,catpath,overwriteFiles=overwriteTasklets)

    def init(self, path="", overwriteImplementation=False, namespacename=None, template=None):

        if path != "":
            self.path = path
        else:
            path = self.path
        j.logger.consoleloglevel = 7

        if namespacename == None:
            for namespacename in j.system.fs.listDirsInDir(path, dirNameOnly=True):
                self.init(path, overwriteImplementation=overwriteImplementation, namespacename=namespacename)
        else:
            # te=j.core.taskletengine.get(j.system.fs.joinPaths("systemtasklets","init"))
            # te.executeV2(osis=self) #will add db & elasticsearch w
            if namespacename[0] == "_":
                return

            self._initDefaultContent(namespacename=namespacename)

            namespacepath = j.system.fs.joinPaths(path, namespacename)
            specpath = j.system.fs.joinPaths(path, namespacename, "model.spec")

            j.core.osis.generateOsisModelDefaults(namespacename, specpath)

            for catname in j.system.fs.listDirsInDir(namespacepath, dirNameOnly=True):
                catpath = j.system.fs.joinPaths(namespacepath, catname)

                # generate model class
                modelfile = j.system.fs.joinPaths(catpath, "model.py")
                if overwriteImplementation or not j.system.fs.exists(path=modelfile):
                    fileFrom = j.system.fs.joinPaths(namespacepath, "model_template.py")
                    if not j.system.fs.exists(fileFrom):
                        fileFrom = j.core.osis.getModelTemplate()
                    j.system.fs.copyFile(fileFrom, modelfile)
                    ed = j.codetools.getTextFileEditor(modelfile)
                    ed.replaceNonRegex("$categoryname", catname.capitalize())
                    ed.save()

                j.core.osis.getOsisModelClass(namespacename, catname)

                # check if there is already an implfile
                implfile = "OSIS_%s_impl.py" % catname
                implpath = j.system.fs.joinPaths(catpath, implfile)
                fileFrom = j.system.fs.joinPaths(namespacepath, "OSIS_category_template.py")
                if overwriteImplementation or not j.system.fs.exists(path=implpath):
                    j.system.fs.copyFile(fileFrom, implpath)

                ed = j.codetools.getTextFileEditor(implpath)
                ed.replaceNonRegex("$namespace", namespacename)
                ed.save()

                classs = j.core.osis._loadModuleClass(implpath)
                if namespacename[0] != "_":
                    osis = classs(self.dbconnections)
                    osis.init(catpath, namespace=namespacename, categoryname=catname)
                    try:
                        modelspec = j.core.specparser.getModelSpec("osismodel", namespacename, catname)
                    except:
                        pass
                    else:
                        osis.create_indexes(modelspec)
                    key = "%s_%s" % (namespacename, catname)
                    self.osisInstances[key] = osis
