from JumpScale import j
import lzma
import msgpack
import os
try:
    import ujson as json
except:
    import json
    
# import 

class BlobStorClient:
    """
    client to blobstormaster
    """

    def __init__(self, master,domain,namespace):        
        self.master=master
        self.domain=domain
        self.namespace=namespace
        self.setGetNamespace()
        self.rmsize=len(self.nsobj["routeMap"])
        self.queue=[]
        self.queuedatasize=0
        self.maxqueuedatasize=1*1024*1024 #1MB
        self._MB4=4*1024*1024
        self._compressMin=32*1024
        self.compress=True
        self.cachepath=""
        self.lastjid=0

        self._downloadbatch={}
        self._downloadbatchSize=0

        self.results={}
        self.blobstor=self._getBlobStorConnection()

        self.errors=[]

    def _normalize(self, path):
        path=path.replace("'","\\'")
        path=path.replace("[","\\[")
        path=path.replace("]","\\]")
        return path

    def setGetNamespace(self,nsobj=None):
        if nsobj==None:            
            ns=self.master.getNamespace(domain=self.domain,name=self.namespace)
            if ns==None:            
                ns=self.master.newNamespace(domain=self.domain,name=self.namespace)        
        else:
            ns=self.master.setNamespace(namespaceobject=nsobj.__dict__)
        self.nsobj=ns
        self.replicaMaxSize=self.nsobj["replicaMaxSizeKB"]*1024
        self.nsid=self.nsobj["id"]
        return ns

    def _getBlobStorConnection(self,datasize=0,random=False):
        return j.clients.blobstor2.getBlobStorConnection(self.master,self.nsobj,datasize,random=random)

    def _execCmd(self,cmd="",args={},data="",sync=True,timeout=60):
        # print "cmd:%s args:%s"%(cmd,args)
        self.lastjid+=1
        if self.lastjid>1000000 and self.results=={}: #cannot have risk to restart the nr when there are results still in mem
            self.lastjid=1

        self.queue.append((self.lastjid,cmd,args,data))
        self.queuedatasize+=len(data)
    
        if sync or len(self.queue)>200 or self.queuedatasize>self.maxqueuedatasize:
            full,res=self._send(sync,timeout)
            
            for jid,val in list(res.items()):
                self.results[jid]=val

            if full:
                #too many to send back at once
                self._getResults()

            self.queue=[]
            self.queuedatasize=0
        
        if sync:
            return self.results.pop(self.lastjid)            
        else:
            return self.lastjid

    def _send(self,sync=False,timeout=60):
        if self.queuedatasize>0:
            print(("send: %s KB nr cmds:%s"%(int(self.queuedatasize/1024),len(self.queue))))
        if len(self.queue)>0:
            full,res=self.blobstor.sendCmds(self.queue,sync=sync,timeout=timeout)
            return full,res
        else:
            return False,None
        


    # def _getResults(self):
    #     for i in range(1000):
    #         res=self.blobstor.sendCmds([(0,"",{},"")],sync=True)
    #         from IPython import embed
    #         print "DEBUG NOW _getResults"
    #         embed()
            
    #         if len(res.keys())==0:
    #             return
    #         for key,val in res.iteritems():
    #             self.results[key]=val #@todo there was something faster to do this
    #     if i>990:
    #         raise RuntimeError("Could not get results, server keeps on sending.")

    def set(self,key, data,repoid=0,sync=True,timeout=60,serialization=""):
        """
        """
        return self._execCmd("SET",{"key":key,"namespace":self.namespace,"repoid":repoid,"serialization":serialization},data=data,sync=sync,timeout=timeout)        

    def sync(self):
        """
        """
        return self._execCmd("SYNC",{"namespace":self.namespace},data="",sync=True,timeout=2)        


    def get(self, key,repoid=0,timeout=60,sync=True):
        """
        get the block back
        """
        res=self._execCmd("GET",{"key":key,"namespace":self.namespace,"repoid":repoid},sync=sync,timeout=timeout) 
        return res

    def existsBatch(self,keys,repoid=0,replicaCheck=False):
        return self._execCmd("EXISTSBATCH",{"keys":keys,"namespace":self.namespace,"repoid":repoid},sync=True,timeout=600) 

    def exists(self,key,repoid=0,replicaCheck=False):
        """
        Checks if the blobstor contains an entry for the given key
        @param key: key to Check
        @replicaCheck if True will check that there are enough replicas (not implemented)
        the normal check is just against the metadata stor on the server, so can be data is lost
        """
        return self._execCmd("EXISTS",{"key":key,"namespace":self.namespace,"repoid":repoid},sync=True,timeout=2)

    def getMD(self,key):
        return self._execCmd("GETMD",{"key":key,"namespace":self.namespace,"repoid":repoid},sync=True,timeout=2) 

    def delete(self,key, repoid=0,force=False):
        return self._execCmd("DELETE",{"key":key,"namespace":self.namespace,"repoid":repoid},sync=True,timeout=60)

    def deleteNamespace(self):
        return self._execCmd("DELNS",{"namespace":self.namespace},sync=True,timeout=600) 

    def _dump2stor(self, data,key="",repoid=0,compress=None):
        if len(data)==0:
            return ""
        if key=="":
            key = j.tools.hash.md5_string(data)
        if compress==True or (len(data)>self._compressMin and self.compress):
            compress=self.compress
            # print "compress"
            print(".")
            data=lzma.compress(data)
            serialization="L"
        else:
            serialization=""

        self.set(key=key, data=data,repoid=repoid,serialization=serialization,sync=False)
        return key

    def _read_file(self,path, block_size=0):
        if block_size==0:
            block_size=self._MB4

        with open(path, 'rb') as f:
            while True:
                piece = f.read(block_size)
                if piece:
                    yield piece
                else:
                    return

    def uploadDir(self,dirpath,compress=False):
        name="backup_md_%s"%j.base.idgenerator.generateRandomInt(1,100000)
        tarpath="/tmp/%s.tar"%name
        if compress:
            cmd="cd %s;tar czf %s ."%(dirpath,tarpath)
        else:
            cmd="cd %s;tar cf %s ."%(dirpath,tarpath)
        j.system.process.execute(cmd)
        key=self.uploadFile(tarpath,compress=False)
        j.system.fs.remove(tarpath)
        return key

    def downloadDir(self,key,dest,repoid=0,compress=None):
        j.system.fs.removeDirTree(dest)
        j.system.fs.createDir(dest)
        name="backup_md_%s"%j.base.idgenerator.generateRandomInt(1,100000)
        tarpath="/tmp/%s.tar"%name
        self.downloadFile(key,tarpath,False,repoid=repoid)
        if compress:
            cmd="cd %s;tar xzf %s"%(dest,tarpath)
        else:
            cmd="cd %s;tar xf %s"%(dest,tarpath)
        j.system.process.execute(cmd)
        j.system.fs.remove(tarpath)

    def uploadFile(self,path,key="",repoid=0,compress=None):
        
        if key=="":
            key=j.tools.hash.md5(path)
        if j.system.fs.statPath(path).st_size>self._MB4:
            hashes=[]
            # print "upload file (>4MB) %s"%(path)
            for data in self._read_file(path):
                hashes.append(self._dump2stor(data,repoid=repoid,compress=compress))
            if len(hashes)>1:
                out = "##HASHLIST##\n"
                hashparts = "\n".join(hashes)
                out += hashparts
                # Store in blobstor
                # out_hash = self._dump2stor(out,key=md5) #hashlist is stored on md5 location of file
                self.set(key=key, data=out,repoid=repoid)   
            else:
                raise RuntimeError("hashist needs to be more than 1.")
        else:
            # print "upload file (<4MB) %s"%(path)
            for data in self._read_file(path):
                self._dump2stor(data,key=key,repoid=repoid,compress=compress)
        return key

    def downloadFile(self,key,dest,link=False,repoid=0, chmod=0,chownuid=0,chowngid=0,sync=False,size=0):

        if self.cachepath!="":
            blob_path = self._getBlobCachePath(key)
            if j.system.fs.exists(blob_path):
                # Blob exists in cache, we can get it from there!
                print(("Blob FOUND in cache: %s" % blob_path))
                if link:
                    self._link(blob_path,dest)
                else:
                    j.system.fs.copyFile(blob_path, dest)
                    os.chmod(dest, chmod)
                    os.chown(dest, chownuid, chowngid)
                return

        if self._downloadbatchSize>self.maxqueuedatasize or len(self._downloadbatch)>200:
            self.downloadBatch()

        #now normally on server we should have results ready

        if size!=0 and sync==False:
            jid=self.get( key,repoid=repoid,sync=False)
            # print [jid,key,dest,link,repoid,chmod,chownuid,chowngid]
            self._downloadbatch[jid]=(jid,key,dest,link,repoid,chmod,chownuid,chowngid)
            self._downloadbatchSize+=int(size)
        else:
            # Get blob from blobstor2 
            if key!="":
                key,serialization,blob = self.get( key,repoid=repoid,sync=True)
                self._downloadFilePhase2(blob,dest,key,chmod,chownuid,chowngid,link,serialization)


    def downloadBatch(self):
        self._send()        
        jids=list(self._downloadbatch.keys())
        self.blobstor._cmdchannel.send_multipart([msgpack.dumps([[0,"getresults",{},jids]]),"S",str(60),self.blobstor.sessionkey])
        res= self.blobstor._cmdchannel.recv_multipart()
       
        for item in res:
            if item=="":
                continue
            else:                
                jid,rcode,result=msgpack.loads(item)
                if rcode==0:
                    jid,key,dest,link,repoid,chmod,chownuid,chowngid=self._downloadbatch[jid]
                    key2=result[0]
                    if key2!=key:
                        raise RuntimeError("Keys need to be the same")
                    blob=result[2]
                    serialization=result[1]
                    
                    self._downloadFilePhase2(blob,dest,key,chmod,chownuid,chowngid,link,serialization)
                else:
                    ##TODO
                    pass

        self._downloadbatchSize=0
        self._downloadbatch={}
            
    def _downloadFilePhase2(self,blob,dest,key,chmod,chownuid,chowngid,link,serialization):
        if key=="":
            return
        if blob==None:
            raise RuntimeError("Cannot find blob with key:%s"%key)
                
        if self.cachepath!="":
            blob_path = self._getBlobCachePath(key)
            self._restoreBlobToDest(blob_path, blob, chmod=chmod,chownuid=chownuid,chowngid=chowngid,serialization=serialization)
            j.system.fs.createDir(j.system.fs.getDirName(dest))

            if link:
                self._link(blob_path,dest)
            else:
                j.system.fs.copyFile(blob_path, dest)            
                os.chmod(dest, chmod) 
                os.chown(dest, chownuid, chowngid) 
        else:
            self._restoreBlobToDest(dest, blob, chmod=chmod,chownuid=chownuid,chowngid=chowngid,serialization=serialization)


    def _getBlobCachePath(self, key):
        """
        Get the blob path in Cache dir
        """
        # Get the Intermediate path of a certain blob
        storpath = j.system.fs.joinPaths(self.cachepath, key[0:2], key[2:4], key)
        return storpath


    def _restoreBlobToDest(self, dest, blob, chmod=0,chownuid=0,chowngid=0,serialization=""):
        """
        Write blob to destination
        """
        check="##HASHLIST##"
        j.system.fs.createDir(j.system.fs.getDirName(dest))
        if blob.find(check)==0:
            # found hashlist
            # print "FOUND HASHLIST %s" % blob
            hashlist = blob[len(check) + 1:]            
            j.system.fs.writeFile(dest,"")
            for hashitem in hashlist.split("\n"):
                if hashitem.strip() != "":
                    key,serialization,blob_block = self.get(hashitem)
                    if serialization=="L":
                         blob_block= lzma.decompress(blob_block)
                    j.system.fs.writeFile(dest, blob_block, append=True)                        
        else:
            # content is there
            if serialization=="L":
                blob = lzma.decompress(blob)
            j.system.fs.writeFile(dest, blob)

        # chmod/chown
        if chmod!=0:
            os.chmod(dest,chmod)
        if chownuid!=0:
            os.chown(dest,chownuid,chowngid)       

    def _link(self, src, dest):
        if dest=="":
            raise RuntimeError("dest cannot be empty")

        os.link(src, dest)

        # j.system.fs.createDir(j.system.fs.getDirName(dest))
        # print "link:%s %s"%(src, dest)

        # if j.system.fs.exists(path=dest):
        #     stat=j.system.fs.statPath(dest)
        #     if stat.st_nlink<2:
        #         raise RuntimeError("only support linked files")
        # else:
        #     cmd="ln '%s' '%s'"%(self._normalize(src),self._normalize(dest))
        #     try:
        #         j.system.process.execute(cmd)
        #     except Exception,e:                
        #         print "ERROR LINK FILE",
        #         print cmd
        #         print e
        #         self.errors.append(["link",cmd,e])
