from JumpScale import j

import time

import JumpScale.baselib.credis

from JumpScale import j
# import JumpScale.grid
# import zmq
import  zmq
import time


class BlobStorServer():

    def __init__(self, port=2345,path="/mnt/BLOBSTOR", nrCmdGreenlets=50):

        j.application.initGrid()

        self.path=path
        
        j.application.initGrid()

        self.adminpasswd = j.application.config.get('grid.master.superadminpasswd')
        self.adminuser = "root"

        #check redis is there if not try to start
        if not j.system.net.tcpPortConnectionTest("127.0.0.1",9999):
            raise RuntimeError("looking for redis on port 9999, could not find")

        def checkblobstormaster():
            masterip=j.application.config.get("grid.master.ip")
            self.master=j.servers.zdaemon.getZDaemonClient(
                masterip,
                port=2344,
                user=self.adminuser,
                passwd=self.adminpasswd,
                ssl=False, sendformat='m', returnformat='m', category="blobstormaster")

        success=False
        while success==False:
            try:
                print "connect to blobstormaster"
                checkblobstormaster()
                success=True
            except Exception,e:
                masterip=j.application.config.get("grid.master.ip")
                msg="Cannot connect to blobstormaster %s, will retry in 60 sec."%(masterip)
                j.events.opserror(msg, category='blobstorworker.startup', e=e)
                time.sleep(60)

        #registration of node & disk

        C="""
blobstor.disk.id=0
blobstor.disk.size=100
""" 
        bsnid=self.master.registerNode(j.application.whoAmI.nid)
        nid=j.application.whoAmI.nid
        for item in j.system.fs.listDirsInDir(self.path, recursive=False, dirNameOnly=False, findDirectorySymlinks=True):
            cfigpath=j.system.fs.joinPaths(item,"main.hrd")
            if not j.system.fs.exists(path=cfigpath):
                j.system.fs.writeFile(filename=cfigpath,contents=C)
            hrd=j.core.hrd.getHRD(path=cfigpath)
            if hrd.get("blobstor.disk.id")=="0":
                sizeGB=j.console.askInteger("please give datasize (GB) for this blobstor mount path:%s"%item)
                diskid=self.master.registerDisk(nid=nid,bsnodeid=bsnid, path=item, sizeGB=sizeGB)
                hrd.set("blobstor.disk.id",diskid)
                hrd.set("blobstor.disk.size",sizeGB)
            else:
                diskid=self.master.registerDisk(nid=nid,bsnodeid=bsnid, path=item, sizeGB=hrd.getInt("blobstor.disk.size"),\
                    diskId=hrd.getInt("blobstor.disk.id"))

        self.port = port

        self.redis=j.clients.blobstor2.redis.redis


    def cmd2Queue(self,qid=0,cmd="",args={},key="",data=""):
        rkeyQ="blobserver:cmdqueue:%s"%qid
        jobguid=j.base.idgenerator.generateGUID()     
        if key<>"":
            args["key"]=key
        job=[int(time.time()),jobguid,cmd,args]        
        if data=="":
            self.blobstor.redis.redis.execute_pipeline(\
                ("RPUSH",rkeyQ,jobguid),\
                ("HSET","blobserver:cmds",jobguid,ujson.dumps(job)))
        elif data<>"":
            self.blobstor.redis.redis.execute_pipeline(\
                ("RPUSH",rkeyQ,jobguid),\
                ("HSET","blobserver:cmds",jobguid,ujson.dumps(job)),\
                ("HSET","blobserver:blob",key,data))
        return jobguid


    def repCmdServer(self):
        cmdsocket = self.cmdcontext.socket(zmq.REP)
        cmdsocket.connect("inproc://cmdworkers")
        while True:
            parts = cmdsocket.recv_multipart()   
            parts=parts[:-1]         
            deny=False
            for part in parts:
                splitted=part.split("\r\n")
                try:
                    cmd=splitted[2]
                    key=splitted[4]
                except Exception,e:
                    raise RuntimeError("could not parse incoming cmds for redis.")

                if cmd not in ("SET","GET","HSET","INCREMENT","RPUSH","LPUSH"):
                    deny=True
                # if key.find("blobstor")<>0:
                #     deny=True
            if deny==True:
                cmdsocket.send_multipart(["DENY"])
            else:
                self.redis.send_packed_commands(parts)
                result =self.redis.read_n_response(len(parts))            
                cmdsocket.send_multipart(result)

    def cmdGreenlet(self):
        # Nonblocking
        self.cmdcontext = zmq.Context()

        cmdsocket = self.cmdcontext.socket(zmq.REP)
        # backend = self.cmdcontext.socket(zmq.DEAL/ER)

        cmdsocket.bind("tcp://*:%s" % self.port)

        while True:
            #Wait for next request from client
            parts = cmdsocket.recv_multipart()   
            parts=parts[:-1]         
            deny=False
            for part in parts:
                splitted=part.split("\r\n")
                try:
                    cmd=splitted[2]
                    key=splitted[4]
                except Exception,e:
                    raise RuntimeError("could not parse incoming cmds for redis.")

                if cmd not in ("SET","GET","HSET","INCREMENT","RPUSH","LPUSH"):
                    deny=True
                # if key.find("blobstor")<>0:
                #     deny=True
            if deny==True:
                cmdsocket.send_multipart(["DENY"])
            else:
                self.redis.send_packed_commands(parts)
                result =self.redis.read_n_response(len(parts))            
                cmdsocket.send_multipart(result)
            


    def start(self):
        # print "starting %s"%self.name
        self.cmdGreenlet()

