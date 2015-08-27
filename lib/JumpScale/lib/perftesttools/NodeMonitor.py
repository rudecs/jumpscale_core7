from JumpScale import j

# import sys
# import time
# import json
# import os
# import psutil
from NodeBase import NodeBase


class NodeMonitor(NodeBase):
    def __init__(self,ipaddr,sshport,name=""): 
        NodeBase.__init__(self,ipaddr=ipaddr,sshport=sshport,role="monitor",name=name)
        if self.name=="":
            self.name="monitor"
        self.startInfluxPump()

    def startInfluxPump(self):  
        env={}

        if  j.tools.perftesttools.monitorNodeIp==None:
            raise RuntimeError("please do j.tools.perftesttools.init() before calling this")

        env["redishost"]=j.tools.perftesttools.monitorNodeIp
        env["redisport"]=9999
        env["idbhost"]="localhost" #influxdb
        env["idbport"]=8086
        env["idblogin"]="root"
        env["idbpasswd"]="root"
        #this remotely let the influx pump work: brings data from redis to influx

        self.prepareTmux("mgmt",["influxpump","mgmt"])
        self.executeInScreen("influxpump","js 'j.tools.perftesttools.influxpump()'",env=env,session="mgmt")   

    def getTotalIOPS(self):
        return (self.getStatObject(key="iops")["val"],self.getStatObject(key="iops_r")["val"],self.getStatObject(key="iops_w")["val"])

    def getTotalThroughput(self):
        return (self.getStatObject(key="kbsec")["val"],self.getStatObject(key="kbsec_r")["val"],self.getStatObject(key="kbsec_w")["val"])
        
    def getStatObject(self,node="total",key="writeiops"):
        data=self.redis.hget("stats:%s"%node,key)
        if data==None:
            return {"val":None}
        data=json.loads(data)
        return data

    def loopPrintStatus(self):
        while True:
            print "total iops:%s (%s/%s)"%self.getTotalIOPS()
            print "total throughput:%s (%s/%s)"%self.getTotalThroughput()
            time.sleep(1)

    # def _runRemote(self):
    #     mypath=os.path.realpath(__file__)
    #     luapath=j.system.fs.joinPaths(j.system.fs.getDirName(mypath),"stat.lua")
    #     j.system.fs.writeFile("/tmp/key",self.key)
    #     print "push scripts & ssh key to monitoring vm."
    #     ftp=self.ssh.getSFtpConnection()
    #     ftp.put(mypath,"/tmp/perftest.py")
    #     ftp.put(luapath,"/tmp/stat.lua")
    #     ftp.put("/tmp/key","/root/.ssh/perftest")
    #     # print "load sshagent"
    #     # self.execute("export SSH_AUTH_SOCK=/root/sshagent_socket;ssh-add /root/.ssh/perftest", dieOnError=False)     
    #     print "start perftest script now on remote"
    #     self.executeInScreen("mgmt","cd /tmp;python perftest.py")    
