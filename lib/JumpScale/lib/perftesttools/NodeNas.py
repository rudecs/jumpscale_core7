from JumpScale import j

# import sys
# import time
# import json
# import os
# import psutil
from NodeBase import NodeBase
from MonitorTools import MonitorTools
from PerfTestTools import *
from MonitorTools import *
from Disk import *

class NodeNas(NodeBase,MonitorTools):
    def __init__(self,ipaddr,sshport=22,nrdisks=0,fstype="xfs"): 
        NodeBase.__init__(self,ipaddr=ipaddr,sshport=sshport,role="nas")
        
        self.disks=[]
        self.nrdisks=nrdisks
        self.fstype=fstype

        self.initDisks()

        self.perftester=PerfTestTools(self)

        self.tmuxinit()

    def startMonitor(self):  
        env={}
        from IPython import embed
        print "DEBUG NOW startMonitor"
        embed()
        
        env["redishost"]=self.redis.addr
        env["redisport"]=self.redis.port
        env["cpu"]=0
        env["disks"]=1
        env["net"]=0
        self.executeInScreen("monitor","js 'j.tools.perftests.monitor()'",env=env)    

    def tmuxinit(self):
        # self.ssh.execute("killall tmux",dieOnError=False)   
        try:  
            self.ssh.execute("tmux kill-session -t perftest")
        except:
            pass
        print "init tmux remote"
        self.ssh.execute("tmux new-session -d -s perftest -n ptest1")            
        
        for i in range(self.nrdisks+1):
            if i!=0: #first disk already done
                print "init tmux screen:%s"%i
                self.ssh.execute("tmux new-window -t 'perftest' -n 'ptest%s'" % (i+1))

        # self.ssh.execute("tmux new-window -t 'perftest' -n 'iostat'")         
        # self.executeInScreen("iostat","apt-get install iotools;iostat -c -d 1")  

    def initDisks(self):
        if testpaths==[] and self.nrdisks>0:
            diskids="bcdefghijklmnopqrstuvwxyz"
            for i in range(self.nrdisks+1):
                diskname="/dev/vd%s"%diskids[i]
                disk=Disk(diskname,node=self,disknr=i+1,screenname="ptest%s"%(i+1))
                self.disks.append(disk)            

            #check mounts
            print "check disks are mounted and we find them all"
            rc,result,err=self.ssh.execute("mount")
            for line in result.split("\n"):
                if line.find(" on ")!=-1 and line.startswith("/dev/v"):# and line.find(self.fstype)!=-1:
                    #found virtual disk
                    devname=line.split(" ")[0]
                    if devname.startswith("/dev/vda"):
                        continue
                    disk=self.findDisk(devname)
                    disk.mounted=True
                    disk.mountpath=line.split(" on ")[1].split(" type")[0].strip()
                    disk.node=self

            for disk in self.disks:
                if disk.mounted==False:
                    disk.initDiskXFS()

                    # raise RuntimeError("Could not find all disks mounted, disk %s not mounted on %s"%(disk,self))


            print "all disks mounted"                    

        else:
            self.nrdisks=0
            i=0
            for mountpath in testpaths:
                disk=Disk("/dummy/%s"%i)
                self.disks.append(disk)            
                disk.screenname="ptest%s"%(i+1)
                disk.disknr=i+1
                disk.mountpath=mountpath
                disk.node=self
                i+=1

    def findDisk(self,devname):
        for disk in self.disks:
            if disk.devname==devname:
                return disk
        raise RuntimeError("cannot find disk:%s"%devname)                