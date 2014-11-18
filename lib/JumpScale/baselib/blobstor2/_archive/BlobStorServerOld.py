from JumpScale import j

import JumpScale.grid.zdaemon

import inspect
import ujson
import tarfile
import tempfile

class BlobserverCMDS():

    def __init__(self, daemon):

        j.application.initGrid()

        self.daemon = daemon
        self.adminpasswd = j.application.config.get('grid.master.superadminpasswd')
        self.adminuser = "root"

        # self.STORpath = "/opt/STOR"  # hardcoded for now needs to come from HRD
        self.name = j.application.appname

        print("APP NAME: %s" % self.name)

        # Just for the sake of running two blobservers on the same node
        # This is how we can distinguish `child` blobserver from `parent` one!
        if self.name == "jumpscale:blobserver2_child":
            self.STORpath = "/opt/STOR"
        else:
            self.STORpath = "/opt/STOR2"

        # j.logger.setLogTargetLogForwarder()

    @property
    def _client(self):
        if self.name != "jumpscale:blobserver2_child":
            return
        return j.servers.zdaemon.getZDaemonClient(
            "127.0.0.1",
            port=2346,
            user=self.adminuser,
            passwd=self.adminpasswd,
            ssl=False, sendformat='m', returnformat='m', category="blobserver")

    def _getPaths(self, namespace, key):
        storpath=j.system.fs.joinPaths(self.STORpath, namespace, key[0:2], key[2:4], key)
        mdpath=storpath + ".md"
        return storpath, mdpath

    def set(self, namespace, key, value, repoId="",serialization="",session=None):
        if serialization=="":
            serialization="lzma"

        storpath,mdpath=self._getPaths(namespace,key)

        if not(key != "" and self.exists(namespace, key)):
            md5 = j.tools.hash.md5_string(value)
            j.system.fs.createDir(j.system.fs.getDirName(storpath))
            j.system.fs.writeFile(storpath, value)


        if not j.system.fs.exists(path=mdpath):
            md={}
            md["md5"] = md5
            md["format"] = serialization
        else:
            md = ujson.loads(j.system.fs.fileGetContents(mdpath))
        if "repos" not in md:
            md["repos"] = {}
        md["repos"][str(repoId)] = True
        mddata = ujson.dumps(md)
        # print "Set:%s"%md
        j.system.fs.writeFile(storpath + ".md", mddata)
        return [key, True, True]

    def get(self, namespace, key, serialization="", session=None):
        if serialization == "":
            serialization = "lzma"

        storpath, mdpath = self._getPaths(namespace,key)

        if not j.system.fs.exists(storpath):
            # Blob doesn't exist here, let's check with Our Parent Blobstor(s)
            if self._client.exists(namespace, key):
                missing_blob = self._client.get(namespace, key, serialization, session)
                # Set the blob in our BlobStor
                self.set(namespace, key, missing_blob, serialization=serialization, session=session)
                return missing_blob

        md = ujson.loads(j.system.fs.fileGetContents(mdpath))
        if md["format"] != serialization:
            raise RuntimeError("Serialization specified does not exist.") #in future can convert but not now
        with open(storpath) as fp:
            data2 = fp.read()
            fp.close()
        return data2

    def getMD(self,namespace,key,session=None):
        if session!=None:
            self._adminAuth(session.user,session.passwd)

        storpath,mdpath=self._getPaths(namespace,key)

        return ujson.loads(j.system.fs.fileGetContents(mdpath))

    def delete(self,namespace,key,repoId="",force=False,session=None):
        if force=='':
            force=False #@todo is workaround default values dont work as properly, when not filled in always ''
        if session!=None:
            self._adminAuth(session.user,session.passwd)

        if force:
            storpath,mdpath=self._getPaths(namespace,key)
            j.system.fs.remove(storpath)
            j.system.fs.remove(mdpath)
            return

        if key!="" and not self.exists(namespace,key):
            return

        storpath,mdpath=self._getPaths(namespace,key)

        if not j.system.fs.exists(path=mdpath):
            raise RuntimeError("did not find metadata")
        md=ujson.loads(j.system.fs.fileGetContents(mdpath))
        if "repos" not in md:
            raise RuntimeError("error in metadata on path:%s, needs to have repos as key."%mdpath)
        if str(repoId) in md["repos"]:
            md["repos"].pop(str(repoId))
        if md["repos"]=={}:
            j.system.fs.remove(storpath)
            j.system.fs.remove(mdpath)
        else:
            mddata=ujson.dumps(md)
            j.system.fs.writeFile(storpath+".md",mddata)

    def exists(self,namespace,key, repoId="", session=None):
        storpath,mdpath=self._getPaths(namespace,key)
        if repoId=="":
            return j.system.fs.exists(path=storpath)
        if j.system.fs.exists(path=storpath):
            md=ujson.loads(j.system.fs.fileGetContents(mdpath))
            return str(repoId) in md["repos"]
        return False

    def deleteNamespace(self, namespace, session=None):
        if session!=None:
            self._adminAuth(session.user,session.passwd)
        storpath=j.system.fs.joinPaths(self.STORpath,namespace)
        j.system.fs.removeDirTree(storpath)

    def getBlobPatch(self, namespace, keyList, session=None):
        """
        Takes a list of Keys, and returns a TAR Archive with All Blobs
        """
        if not keyList:
            raise RuntimeError("Invalid Blobs Key List")

        patch_name = tempfile.mktemp(prefix="blob", suffix=".tar")
        blob_patch = tarfile.open(patch_name, 'w')

        for key in keyList:
            blob_path, _ = self._getPaths(namespace, key)
            if j.system.fs.exists(blob_path):
                # TODO: change blob_path to be easier in extraction instead of full path
                # Now it is added as /opt/STOR/<namespace>/<key0:2>/<key2:4>/<key>
                blob_patch.add(blob_path)

        blob_patch.close()

        # TODO: What if very large Tar?!
        with open(patch_name) as fp:
            data = fp.read()
            fp.close()

        return data

    def _adminAuth(self,user,passwd):
        if user != self.adminuser or passwd != self.adminpasswd:
            raise RuntimeError("permission denied")


class BlobStorServer2:
    """
    """

    def __init__(self, port=2345):
        daemon = j.servers.zdaemon.getZDaemon(port=port)

        daemon.setCMDsInterface(BlobserverCMDS, category="blobserver")  # pass as class not as object !!! chose category if only 1 then can leave ""

        #cmds=daemon.daemon.cmdsInterfaces["blobserver"][0]
        # cmds.loadJumpscripts()

        daemon.start()

