from JumpScale import j

# import sys
# import time
# import json
# import os
# import psutil

from MonitorTools import *

class NodeBase(MonitorTools):
    def __init__(self,ipaddr,sshport=22,role=None,name=""):
        """
        existing roles
        - vnas
        - monitor
        - host

        """

        if  j.tools.perftesttools.monitorNodeIp==None:
            raise RuntimeError("please do j.tools.perftesttools.init() before calling this")
        self.redis=j.clients.redis.getRedisClient(j.tools.perftesttools.monitorNodeIp, j.tools.perftesttools.monitorNodeSSHPort, \
            password=j.tools.perftesttools.redispasswd)

        self.key=j.tools.perftesttools.sshkey
        self.name=name

        self.ipaddr=ipaddr
        self.sshport = sshport

        self.ssh=j.remote.ssh.getSSHClientUsingSSHAgent(host=ipaddr, username='root', port=sshport, timeout=10)
        # self._initFabriclient()
        # self.sal=j.ssh.unix.get(self.ssh)
        self.role=role



    def startMonitor(self,cpu=1,disks=[],net=1):
        self.prepareTmux("mon%s"%self.role,["monitor"])      
        env={}
        if  j.tools.perftesttools.monitorNodeIp==None:
            raise RuntimeError("please do j.tools.perftesttools.init() before calling this")
        env["redishost"]=j.tools.perftesttools.monitorNodeIp
        env["redisport"]=9999
        env["cpu"]=cpu
        env["disks"]=",".join(disks)
        env["net"]=net
        env["nodename"]=self.name
        self.executeInScreen("monitor","js 'j.tools.perftesttools.monitor()'",env=env)    

    def execute(self,cmd, env={},dieOnError=True,report=True):
        if report:
            print cmd
        return self.ssh.execute(cmd, dieOnError=dieOnError)
        # if dieOnError:
        #     self.fabric.env['warn_only'] = True
        # res= self.ssh.run(cmd, dieOnError=dieOnError,env=env)
        # if dieOnError:
        #     self.fabric.env['warn_only'] = False
        # return res

    def prepareTmux(self,session,screens=["default"],kill=True):
        print "prepare tmux:%s %s %s"%(session,screens,kill)
        if len(screens)<1:
            raise RuntimeError("there needs to be at least 1 screen specified")
        if kill:
            self.execute("tmux kill-session -t %s"%session, dieOnError=False)

        self.execute("tmux new-session -d -s %s -n %s"%(session,screens[0]), dieOnError=True)

        screens.pop(0)

        for screen in screens:
            print "init tmux screen:%s"%screen
            self.execute("tmux new-window -t '%s' -n '%s'" %(session,screen))

    def executeInScreen(self,screenname,cmd,env={},session=""):
        """
        gets executed in right screen for the disk
        """
        envstr="export "
        if env!={}:
            #prepare export arguments
            for key,val in env.iteritems():
                envstr+="export %s=%s;"%(key,val)
            envstr=envstr.strip(";")
        cmd1="cd /tmp;%s;%s"%(envstr,cmd)
        cmd1=cmd1.replace("'","\"")
        windowcmd=""
        if session!="":
            windowcmd="tmux select-window -t \"%s\";"%session
        cmd2="%stmux send-keys -t '%s' '%s\n'"%(windowcmd,screenname,cmd1)
        # print cmd2
        print "execute:'%s' on %s in screen:%s/%s"%(cmd1,self,session,screenname)
        self.execute(cmd2,report=False)

    def _initFabriclient(self):
        c = j.remote.cuisine
        self.fabric = c.fabric        

        if self.key:
            self.fabric.env["key"] = self.key
        # else:
        #     self.fabric.env["key_filename"] = '/root/.ssh/id_rsa.pub'

        # self.fabric.env['use_ssh_config'] = True
        self.fabric.env['user'] = 'root'

        self.cuisine = c.connect(self.ipaddr, self.sshport)

    def __str__(self):
        return "node:%s"%self.ipaddr

    def __repr__(self):
        return self.__str__()
