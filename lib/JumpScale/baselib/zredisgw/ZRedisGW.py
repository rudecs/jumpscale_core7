from JumpScale import j

import time

import JumpScale.baselib.credis

from JumpScale import j
# import JumpScale.grid
# import zmq
import gevent
import gevent.monkey
import zmq.green as zmq
import time
try:
    import ujson as json
except:
    import json

GeventLoop = j.core.gevent.getGeventLoopClass()

#@needs to be debugged

class ZRedisGW(GeventLoop):

    def __init__(self, port=2345,path="/mnt/BLOBSTOR", nrCmdGreenlets=50):

        j.application.initGrid()

        self.adminpasswd = j.application.config.get('grid.master.superadminpasswd')
        self.adminuser = "root"

        #check redis is there if not try to start
        if not j.system.net.tcpPortConnectionTest("127.0.0.1",9999):
            j.packages.findNewest(name="redis").install()
            j.packages.findNewest(name="redis").start()

        gevent.monkey.patch_socket()
        GeventLoop.__init__(self)

        self.port = port
        self.nrCmdGreenlets = nrCmdGreenlets

        #self.redis=...

        

    def cmd2Queue(self,qid=0,cmd="",args={},key="",data="",sync=True):
        rkeyQ="blobserver:cmdqueue:%s"%qid
        jobguid=j.base.idgenerator.generateGUID()     
        if key<>"":
            args["key"]=key
        job=[int(time.time()),jobguid,cmd,args]        
        if data=="":
            self.blobstor.redis.redis.execute_pipeline(\
                ("RPUSH","blobserver:cmdqueue:0",jobguid),\
                ("HSET","blobserver:cmds",jobguid,json.dumps(job)))
        elif data<>"":
            self.blobstor.redis.redis.execute_pipeline(\
                ("RPUSH",rkeyQ,jobguid),\
                ("HSET","blobserver:cmds",jobguid,json.dumps(job)),\
                ("HSET","blobserver:blob",key,data))
        if sync:
            self.blobstor.redis.redis.execute(cmd="BLPOP", key="blobserver:return:%s"%jobguid)
            self.blobstor.redis.redis.execute(cmd="HDEL", key="blobserver:cmds",subkey=jobguid)
        return jobguid


    #         result=self.queueCMD(cmd="BLPOP", key="blobserver:return:%s"%jobguid, data=timeout,sendnow=True)
    #         self.queueCMD(cmd="HDEL", key="blobserver:cmds",subkey=jobguid) 

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
                    if len(splitted)>4:
                        key=splitted[4]
                    else:
                        key=""
                except Exception,e:                    
                    raise RuntimeError("could not parse incoming cmds for redis. Error:%s"%e)

                # if cmd not in ("SET","GET","HSET","INCREMENT","RPUSH","LPUSH"):
                #     deny=True
                # if key.find("blobstor")<>0:
                #     deny=True
            if deny==True:
                cmdsocket.send_multipart(["DENY"])
            else:
                self.redis.send_packed_commands(parts)
                result =self.redis.read_n_response(len(parts))            
                if j.basetype.list.check(result[-1]):
                    result=result[-1]
                cmdsocket.send_multipart(result)

    def cmdGreenlet(self):
        # Nonblocking
        self.cmdcontext = zmq.Context()

        frontend = self.cmdcontext.socket(zmq.ROUTER)
        backend = self.cmdcontext.socket(zmq.DEALER)

        frontend.bind("tcp://*:%s" % self.port)
        backend.bind("inproc://cmdworkers")

        # Initialize poll set
        poller = zmq.Poller()
        poller.register(frontend, zmq.POLLIN)
        poller.register(backend, zmq.POLLIN)

        workers = []

        for i in range(self.nrCmdGreenlets):
            workers.append(gevent.spawn(self.repCmdServer))

        while True:
            socks = dict(poller.poll())
            if socks.get(frontend) == zmq.POLLIN:
                parts = frontend.recv_multipart()
                parts.append(parts[0])  # add session id at end
                backend.send_multipart([parts[0]] + parts)

            if socks.get(backend) == zmq.POLLIN:
                parts = backend.recv_multipart()
                frontend.send_multipart(parts[1:])  # @todo dont understand why I need to remove first part of parts?

    def start(self, mainloop=None):
        # print "starting %s"%self.name
        self.schedule("cmdGreenlet", self.cmdGreenlet)
        # self.startClock()
        # print "start %s on port:%s"%(self.name,self.port)
        if mainloop <> None:
            mainloop()
        else:
            while True:
                gevent.sleep(100)

