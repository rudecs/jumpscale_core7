from JumpScale import j

from .ZRedisGWClient import *
# from ZRedisGWServer import *


import JumpScale.baselib.credis

# import msgpack

# _pack_pipeline_command

import JumpScale.grid.zdaemon

BSTRANSPPARENT=j.core.zdaemon.getZDaemonTransportClass()
class ZRedisGWTransport(BSTRANSPPARENT):

    def __init__(self,addr,port,gevent=True):
        BSTRANSPPARENT.__init__(self,addr=addr,port=port,gevent=gevent)
        self._init()
        # self.redis=j.clients.redis2.redis.redis
        self.packcmds=j.clients.redis2.redis.redis.pack_pipeline_command_list

    def sendCmds(self,cmds,transaction=True):
        """
        list of cmds, each cmd is a tuple which can be understood by redis
        """
        if transaction and len(cmds)>0:
            cmds.insert(0,("MULTI",))
            cmds.append(("EXEC",))
            
        args=self.packcmds(cmds)

        self._cmdchannel.send_multipart(args)
        result=self._cmdchannel.recv_multipart()

        
        if result[0]=="DENY":
            raise RuntimeError("cmds could not be send, access denied.")
        else:
            return result

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
        c=self._getZRedisGWConnection(datasize=self.queuedatasize)
        res=c.sendCmds(self.queue,transaction=True)
        self.queue=[]
        self.queuedatasize=0
        return res            


class ZRedisGWFactory:
    def __init__(self):
        self.logenable=True
        self.loglevel=5
        self._redisCache={}
        self.redis = j.clients.credis.getRedisClient("127.0.0.1", 9999,timeout=2)

    def getZRedisGWConnection(self,ipaddr,port,login,passwd):
        key="%s_%s"%(ipaddr,port)
        if key in self._redisCache:
            return self._redisCache[key]      
        self._redisCache[key]=  ZRedisGWTransport(addr=ipaddr,port=port,gevent=True)
        return self._redisCache[key]

    def log(self,msg,category="",level=5):
        if level<self.loglevel+1 and self.logenable:
            j.logger.log(msg,category="redis.%s"%category,level=level)

    def start(self,port=2345):
        bss=ZRedisGWServer(port=port)
        bss.start()

