from JumpScale import j

# import sys
# import time
# import json
# import os
# import psutil
from NodeBase import NodeBase
from MonitoringTools import MonitoringTools


class NodeMonitor(NodeBase,MonitorTools):
    def __init__(self,ipaddr,sshport=22,redis=None): 
        NodeBase.__init__(self,ipaddr=ipaddr,sshport=sshport,redis=redis,role="monitor")
        self.tmuxinit()
        self.startRedis2Influxdb()

    def startRedis2Influxdb(self):  
        env={}
        from IPython import embed
        print "DEBUG NOW startRedis2Influxdb"
        embed()
        
        env["redishost"]=self.redis.addr
        env["redisport"]=self.redis.port
        env["idbhost"]=self.redis.addr
        env["idbport"]=self.redis.port
        env["idblogin"]="root"
        env["idbpasswd"]="root"
        self.executeInScreen("influxpump","js 'j.tools.perftests.influxpump()'",env=env)   

    def tmuxinit(self):
        if self.remote:
            # self.ssh.execute("tmux kill-session -t mgmt", dieOnError=False)
            self.ssh.execute("tmux new-session -d -s mgmt -n mgmt", dieOnError=False)
            self._runRemote()
        else:
            self.ssh.execute("tmux kill-session -t influxpump", dieOnError=False)
            self.ssh.execute("tmux new-session -d -s influxpump -n influxpump")

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

    def _runRemote(self):
        mypath=os.path.realpath(__file__)
        luapath=j.system.fs.joinPaths(j.system.fs.getDirName(mypath),"stat.lua")
        j.system.fs.writeFile("/tmp/key",self.key)
        print "push scripts & ssh key to monitoring vm."
        ftp=self.ssh.getSFtpConnection()
        ftp.put(mypath,"/tmp/perftest.py")
        ftp.put(luapath,"/tmp/stat.lua")
        ftp.put("/tmp/key","/root/.ssh/perftest")
        # print "load sshagent"
        # self.execute("export SSH_AUTH_SOCK=/root/sshagent_socket;ssh-add /root/.ssh/perftest", dieOnError=False)     
        print "start perftest script now on remote"
        self.executeInScreen("mgmt","cd /tmp;python perftest.py")    
