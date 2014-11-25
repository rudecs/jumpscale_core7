from JumpScale import j

import JumpScale.grid.zdaemon

# import inspect
try:
    import ujson as json
except:
    import json

# import JumpScale.baselib.redisworker
# import marisa_trie


class BlobstorMasterCMDS():

    def __init__(self, daemon):
        j.application.initGrid()
        self.daemon = daemon
        self.blobstor=j.clients.blobstor2
        self.nodes=self.blobstor.nodes
        self.disks=self.blobstor.disks

    def _load(self):
        result=self.blobstor._getNodesDisks()
        if result!=None:
            self.nodes,self.disks=result
        else:
            for guid in self.osis.node.list():
                obj=self.osis.node.get(guid)
                if obj.gid==j.application.whoAmI.gid:
                    obj.__dict__.pop("_meta")
                    obj.__dict__.pop("_ckey")
                    obj.size=0
                    obj.free=0
                    self.nodes[str(obj.id)]=obj.__dict__
            for guid in self.osis.disk.list():
                obj=self.osis.disk.get(guid)
                obj.__dict__.pop("_meta")
                obj.__dict__.pop("_ckey")
                if obj.gid==j.application.whoAmI.gid:
                    if obj.free==0:
                        obj.free=100 #is for not to continue, need to read better from FS
                    if not obj.size==0:
                        node=self.nodes[str(obj.bsnodeid)]
                        node["size"]+=obj.size
                        node["free"]+=obj.free
                        self.disks[str(obj.id)]=obj.__dict__
            self.blobstor._setNodesDisks()

    def getNodesDisks(self,session=None):
        self._load()
        return [self.nodes,self.disks]

    def _checkNS(self,ns):
        """
        how do we define the spread
        we try to create a large as possible spread but max = spreadnr
        we go over nodes in spreadmap, see which nodes are still usable in spread (if not we remove from spread)
        now we sort the nodes in grid from larges free size to smalles, they will be used to try and append to the spread until we have enough
        if not possible to have enough then we will put in what we have if more than 0
        """
        self._load()
        spreadnr=int(ns["spreadpolicy"].split("/")[0])
        freetot=0
        nodes2remove=[]
        for nodeid in ns["routeMap"]:
            if nodeid not in self.nodes:
                #means node is no longer available (e.g. full, or down)
                nodes2remove.append(nodeid)
            else:
                node=self.nodes[nodeid]
                if node["free"]<500:
                    nodes2remove.append(nodeid)
                else:
                    freetot+=node["free"]
        if freetot<1000:
            #create a complete new map, the nodes are almost empty
            nodes2remove=ns["routeMap"]
        for node2remove in nodes2remove:
            #remove nodes which do not comply (not enough storage available)
            ns["routeMap"].pop(ns['routeMap'].index(node2remove))

        if len(ns["routeMap"])>spreadnr-1:
            return ns #nothing todo spread is ok

        nkeys=list(self.nodes.keys())
        tosort=[]
        def tostr(iint):
            iint=str(iint)
            while len(iint)<8:
                iint="0%s"%iint
            return iint
        for key,node in list(self.nodes.items()):
            tosort.append("%s_%s"%(tostr(node["free"]),key))
        tosort.sort()
        tosort.reverse()

        rm=ns["routeMap"]
        x=0
        while len(rm)<spreadnr:
            if x<len(tosort):
                free,key=tosort[x].split("_")
                key=int(key)
                rm.insert(0,key)
                x+=1
            else:
                #nothing further to find, we are not safe
                ns["nodeSafe"]=False 
                break

        if len(rm)==0:
            raise RuntimeError("Could not find spread, no free space")
        return ns
    
    def registerNode(self,nid,session=None):
        node=self.osis.node.new()
        node.gid=j.application.whoAmI.gid
        node.nid=nid
        nodeguid,temp,temp=self.osis.node.set(node)
        bsnid= int(nodeguid.split("_")[1])
        return bsnid
    
    def getNodeLoginDetails(self,bsnid,session=None):
        """
        returns (ipaddr,port,key)
        """
        bsnid=str(bsnid)
        if bsnid not in self.nodes:
            raise RuntimeError("Could not find node with id:%s"%bsnid)
        node=self.nodes[bsnid]

        gridnode=self.osis.gridnode.get("%s_%s"%(j.application.whoAmI.gid,node["nid"]))

        return (gridnode.ipaddr,2345,"1234")

    def registerDisk(self,nid, bsnodeid, path, sizeGB,diskId=None,session=None):
        if diskId==None:
            disk=self.osis.disk.new()
        else:
            diskId=str(diskId)
            disk=self.osis.disk.get("%s_%s"%(j.application.whoAmI.gid,diskId))

        disk.gid=j.application.whoAmI.gid
        disk.nid=nid
        disk.bsnodeid=bsnodeid
        disk.size=int(sizeGB)
        disk.path=path
        diskguid,temp,temp=self.osis.disk.set(disk)
        diskid= int(diskguid.split("_")[1])        
        return diskid

    def getNamespace(self,domain,name,session=None):
        ns=self.blobstor._getNS(domain,name)
        if ns==None:
            gid=j.application.whoAmI.gid
            result=self.osis.namespace.simpleSearch({"gid":gid,"name":name,"domain":domain},withguid=True)
            if len(result)>1:
                raise RuntimeError("Found more than 1 names space: %s/%s in ES. Illegal."%(domain,name))
            elif len(result)==1:
                ns=self.osis.namespace.get(result[0]["guid"])
                ns=self._checkNS(ns.__dict__)
                self.blobstor._setNS(ns)
                return  ns
        return None
          
    def getNamespaceFromId(self,nsid,session=None):
        ##TODO
        return  ns

    def newNamespace(self,domain,name,session=None):
        obj=self.osis.namespace.new()
        obj.name=name
        obj.gid=j.application.whoAmI.gid
        obj.domain=domain
        guid,temp,temp=self.osis.namespace.set(obj)
        ns=self.osis.namespace.get(guid)
        ns=self._checkNS(ns.__dict__)
        return  ns

    def setNamespace(self,namespaceobject,session=None):
        namespaceobject["gid"]=j.application.whoAmI.gid
        guid,temp,temp=self.osis.namespace.set(namespaceobject)
        ns=self.osis.namespace.get(guid)
        ns=self._checkNS(ns.__dict__)
        return  ns

    def setMDSet(self,domain,name,blobkey,gitlabip="",gitlabaccount="",gitlabreponame="",gitlabpasswd=""):
        """
        @return key of the mdset (metadata set)
        """
        ##TODO
        pass
        

    def setMDSet(self,mdset_key):
        ##TODO
        pass
        

class OsisGroup():
    pass

class BlobStorMaster:
    """
    """

    def __init__(self, port=2344):
        self.port=port


    def start(self):

        #check redis is there if not try to start
        if not j.system.net.tcpPortConnectionTest("127.0.0.1",9999):
            j.packages.findNewest(name="redis").install()
            j.packages.findNewest(name="redis").start()

        def checkosis():
            self.osis = j.core.osis.getClientByInstance('main')

        if 'jumpscale__osis' in j.tools.startupmanager.listProcesses():
            j.tools.startupmanager.startProcess("jumpscale","osis")

        masterip=j.application.config.get("grid.master.ip")
        if masterip in j.system.net.getIpAddresses():

            if not j.tools.startupmanager.exists("jumpscale","osis"):
                raise RuntimeError("Could not find osis installed on local system, please install.")
            
            if not j.system.net.tcpPortConnectionTest("127.0.0.1",5544):
                j.tools.startupmanager.startProcess("jumpscale","osis")

        success=False
        while success==False:
            try:
                checkosis()
                success=True
            except Exception as e:
                msg="Cannot connect to osis %s, will retry in 60 sec."%(masterip)
                j.events.opserror(msg, category='processmanager.startup', e=e)
                time.sleep(60)

        daemon = j.servers.zdaemon.getZDaemon(port=self.port)

        daemon.addCMDsInterface(BlobstorMasterCMDS, category="blobstormaster")  # pass as class not as object !!! chose category if only 1 then can leave ""

        daemon.daemon.cmdsInterfaces["blobstormaster"].osis=OsisGroup()
        osis=daemon.daemon.cmdsInterfaces["blobstormaster"].osis

        osis.node=j.core.osis.getClientForCategory(self.osis,"blobstor","bsnode")
        osis.namespace=j.core.osis.getClientForCategory(self.osis,"blobstor","bsnamespace")
        osis.disk=j.core.osis.getClientForCategory(self.osis,"blobstor","bsdisk")
        osis.mdset=j.core.osis.getClientForCategory(self.osis,"blobstor","mdset")
        osis.gridnode=j.core.osis.getClientForCategory(self.osis,"system","node")


        daemon.start()

