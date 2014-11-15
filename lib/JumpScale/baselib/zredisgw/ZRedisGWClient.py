from JumpScale import j

try:
    import ujson as json
except:
    import json

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
        self.key=None #toimplement
        self.queue=[]
        self.queuedatasize=0
        self.maxqueuedatasize=1*1024*1024 #1MB

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

    def _getBlobStorConnection(self,datasize=0):
        return j.clients.blobstor2.getBlobStorConnection(self.master,self.nsobj,datasize)

    def exists(self,key,replicaCheck=False):
        """
        Checks if the blobstor contains an entry for the given key
        @param key: key to Check
        @replicaCheck if True will check that there are enough replicas
        the normal check is just against the metadata stor on the server, so can be data is lost
        """
        c=self._getBlobStorConnection(datasize)
        return c.exists(key=key, data=data,nsid=self.nsid,replicaCheck=replicaCheck)

    def queueCMD(self,cmd,key,data="",subkey="",sendnow=False):
        if data=="":
            self.queue.append((cmd,key))
        else:
            if subkey=="":
                self.queue.append((cmd,key,data))
            else:
                self.queue.append((cmd,key,subkey,data))
            self.queuedatasize+=len(data)
        if sendnow or len(self.queue)>100 or self.queuedatasize>self.maxqueuedatasize:
            self.sendNow()

    def sendNow(self):
        c=self._getBlobStorConnection(datasize=self.queuedatasize)
        res=c.sendCmds(self.queue,transaction=True)
        self.queue=[]
        self.queuedatasize=0
        return res

    def getMD(self,key):
        c=self._getBlobStorConnection(datasize)
        return c.getMD( key=key,nsid=self.nsid)

    def delete(self,key, datasize=0,force=False):
        c=self._getBlobStorConnection(datasize)
        return c.delete(key=key,nsid=self.nsid,force=force)

    # def _getJob(self,cmd,args={},key=""):
    #     jobguid=j.base.idgenerator.generateGUID()     
    #     if key<>"":
    #         args["key"]=key
    #     job=[int(time.time()),jobguid,cmd,args] 
    #     return (jobguid,ujson.dumps(job))

    # def _execCmd(self,qid=0,cmd="",args={},key="",data="",sendnow=True,sync=True,timeout=10):
    #     jobguid,job=self._getJob("set",key=key)           
    #     if data=="":
    #         self.queueCMD(cmd="RPUSH", key="blobserver:cmdqueue:0", data=jobguid)
    #         self.queueCMD(cmd="HSET", key="blobserver:cmds",subkey=jobguid, data=job)
    #     elif data<>"":
    #         self.queueCMD(cmd="RPUSH", key="blobserver:cmdqueue:0", data=jobguid)
    #         self.queueCMD(cmd="HSET", key="blobserver:cmds",subkey=jobguid, data=job)
    #         self.queueCMD(cmd="HSET", key="blobserver:blob", subkey=key,data=data)

    #     if sync:
    #         result=self.queueCMD(cmd="BLPOP", key="blobserver:return:%s"%jobguid, data=timeout,sendnow=True)
    #         self.queueCMD(cmd="HDEL", key="blobserver:cmds",subkey=jobguid) 
    #         return result[-1]
    #     else:   
    #         if sendnow:
    #             result=self.sendNow()
    #         else:
    #             result=None

    #         return jobguid,result


    def set(self,key, data,sendnow=True,sync=True,timeout=60):
        """
        """
        return self._execCmd(0,"SET",{},key=key,data=data,sendnow=sendnow,sync=sync,timeout=timeout)        

    def get(self, key,timeout=60):
        """
        get the block back
        """
        return self._execCmd(0,"GET",{},key=key,sendnow=True,sync=True,timeout=timeout)  

    def existsBatch(self,keys,replicaCheck=False):
        c=self._getBlobStorConnection()
        return c.existsBatch(keys=keys,nsid=self.nsid,replicaCheck=replicaCheck)

    def deleteNamespace(self):
        c=self._getBlobStorConnection()
        return c.deleteNamespace(nsid=self.nsid)


