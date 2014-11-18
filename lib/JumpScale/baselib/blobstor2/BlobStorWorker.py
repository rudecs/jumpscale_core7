from JumpScale import j

import JumpScale.grid.zdaemon

import inspect
import ujson
import tarfile
import tempfile
import JumpScale.baselib.redisworker
import marisa_trie

def populateExistsCache(stor):
    from JumpScale import j
    import marisa_trie

    w=j.base.fswalker.get()

    keys=[]
    mmax=1000000
    nr=1

    mtreepath="%s/mtreestmp/"%stor
    mtreepathProd="%s/mtrees/"%stor

    j.system.fs.removeDirTree(mtreepath)
    j.system.fs.createDir(mtreepath)

    def writetree(keys,nr):
        tree=marisa_trie.Trie(keys)
        tree.save("%s/%s.mtree"%(mtreepath,nr))
        nr+=1
        return nr

    def processfile(path,stat,arg):
        keys=arg["keys"]  
        nr=arg["nr"]      
        if path[-3:]==".md":
            md5=j.system.fs.getBaseName(path)[:-3]
            keys.append(md5)        
        if len(keys)>mmax:
            nr=writetree(keys,nr)
            keys=[]

    callbackFunctions={}
    callbackFunctions["F"]=processfile

    arg={}
    arg["keys"] =keys
    arg["nr"] =nr
    w.walk(stor,callbackFunctions,arg=arg)#,childrenRegexExcludes=[".*/.git/.*"])

    nr=writetree(keys,nr)

    j.system.fs.removeDirTree(mtreepathProd)
    j.system.fs.renameDir(mtreepath,mtreepathProd)

    #try to reclaim mem    
    del keys
    import gc
    gc.collect()

    # import resource
    # mem=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


class BlobStorWorker:
    """
    will read from disk & then poll queue on redis for work
    """

    def __init__(self, path="/mnt/BLOBSTOR",id=1):
        """
        if id==0 then the worker will do the dispatching work
        if id>0 it means worker will be doing io
        """

        self.path=path
        
        j.application.initGrid()

        #check redis is there if not try to start
        if not j.system.net.tcpPortConnectionTest("127.0.0.1",9999):
            j.packages.findNewest(name="redis").install()
            j.packages.findNewest(name="redis").start()

        self.blobstor=j.clients.blobstor2
        self.master=self.blobstor.getMasterClient() #@todo need to work with right connection, now default
        self.blobstor.getNodesDisks() #load all known nodes & disks of grid for blobstor
        self.redis=self.blobstor.redis

        # from IPython import embed
        # print "DEBUG NOW kkkk"
        # embed()
        



    def _getPaths(self, namespace, key):
        storpath=j.system.fs.joinPaths(self.STORpath, namespace, key[0:2], key[2:4], key)
        mdpath=storpath + ".md"
        return storpath, mdpath


    # def populateExistsCache(self,namespace="backup"):
    #     print "POPULATE CACHE CAN TAKE A LONG TIME"
    #     stor=j.system.fs.joinPaths(self.STORpath, namespace)
    #     result=j.clients.redisworker.execFunction( method=populateExistsCache, _category='populateExistsCache', _organization='blobserver2', _timeout=1200, _queue='io', _log=True,_sync=True, stor=stor)
    #     self.loadExistsCache(namespace)
    #     # populateExistsCache(stor=j.system.fs.joinPaths(self.STORpath, namespace))

    # def loadExistsCache(self,namespace="backup"):
    #     stor=self.STORpath
    #     mtreepathProd="%s/%s/mtrees/"%(stor,namespace)
    #     nr=1
    #     path="%s/%s.mtree"%(mtreepathProd,nr)
    #     while j.system.fs.exists(path):
    #         trie = marisa_trie.Trie()
    #         trie.load("%s/%s.mtree"%(mtreepathProd,nr))
    #         if not self.mtrees.has_key(namespace):
    #             self.mtrees[namespace]=[]
    #         self.mtrees[namespace].append(trie)
    #         nr+=1
    #         path="%s/%s.mtree"%(mtreepathProd,nr)

    def existsBatch(self,namespace,keys,repoId="",session=None):
        if namespace not in self.mtrees:
            self.populateExistsCache(namespace)

        notfound=[]

        for key in keys:
            exists=False
            for tree in self.mtrees[namespace]:
                if tree.get(key)!=None:
                    exists=True
                    continue
            if exists==False:
                #check on fs
                exists=self.exists(namespace,keys,repoId)

            if exists==False:
                notfound.append(key)
                
        return notfound        

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

