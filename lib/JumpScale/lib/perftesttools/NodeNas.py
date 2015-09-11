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

class NodeNas(NodeBase):
    def __init__(self,ipaddr,sshport=22,nrdisks=0,fstype="xfs",debugdisk="",name=""): 
        NodeBase.__init__(self,ipaddr=ipaddr,sshport=sshport,role="nas",name=name)
        
        self.debugdisk=debugdisk
        if self.debugdisk!="":
            self.debug=True
        self.disks=[]
        self.nrdisks=int(nrdisks)
        self.fstype=fstype

        self.initDisks()


        self.perftester=PerfTestTools(self)

        disks=[item.devnameshort for item in self.disks]
        self.startMonitor(disks=disks)

        self.initTest()

    def initTest(self):
        screens=[]
        for i in range(self.nrdisks):
            screens.append("ptest%s"%i)
        self.prepareTmux("perftest",screens)

    def initDisks(self):

        if self.debug==False:
            diskids="bcdefghijklmnopqrstuvwxyz"
            for i in range(self.nrdisks):
                diskname="/dev/vd%s"%diskids[i]
                disk=Disk(diskname,node=self,disknr=i+1,screenname="ptest%s"%(i))
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
                    if disk!=None:
                        disk.mounted=True
                        disk.mountpath=line.split(" on ")[1].split(" type")[0].strip()
                        disk.node=self

            for disk in self.disks:
                if disk.mounted==False:
                    disk.initDiskXFS()

                    # raise RuntimeError("Could not find all disks mounted, disk %s not mounted on %s"%(disk,self))


            print "all disks mounted"                    

        else:            
            i=0
            disk=Disk(self.debugdisk)
            self.disks.append(disk)            
            disk.screenname="ptest%s"%i
            disk.disknr=i+1
            disk.mountpath="/tmp/dummyperftest/%s"%i
            j.system.fs.createDir(disk.mountpath)
            disk.node=self

    def findDisk(self,devname):
        for disk in self.disks:
            if disk.devname==devname:
                return disk
        return None
