from JumpScale import j

# import sys
# import time
# import json
# import os


class Disk():
    def __init__(self,devname,node=None,disknr=None,screenname=None):
        devname.replace("//","/")
        self.devname=devname
        self.devnameshort=self.devname.split("/")[2]
        self.mounted=False
        self.mountpath=None
        self.node=node
        self.disknr=disknr
        self.screenname=screenname
        # print "init disk:%s"%self

    def initDiskXFS(self):
        print "initxfs:%s"%self
        res=self.node.ssh.execute("lsblk -f |grep %s"%self.devnameshort, dieOnError=False)[1].strip()
        if res=="":
            #did not find formatted disk
            self.node.ssh.execute("mkfs.xfs -f /dev/%s"%self.devnameshort)
        elif res.find("xfs")==-1:
            #did find but no xfs
            self.node.ssh.execute("mkfs.xfs -f /dev/%s"%self.devnameshort)

        self.mount()

        print "initxfs:%s check mount"%self
        if not self.checkMount():
            raise RuntimeError("could not mount %s"%self)
        print "initxfs:%s done"%self

    def mount(self):
        print "mount:%s mounting %s on %s " % (self, self.devname, self.disknr
        mountpath = 
        self.node.ssh.execute("mkdir -p /storage/%s" % self.mountpath)
        self.node.ssh.execute("mount %s /storage/%s" % (self.devname,self.disknr), dieOnError=False)


    def checkMount(self):
        rc,result,err=self.node.ssh.execute("mount")
        for line in result.split("\n"):
            if line.find(" on ")!=-1 and line.startswith(self.devname) and line.find(self.node.fstype)!=-1:
                return True
        return False

    def execute(self,cmd,env={}):
        """
        gets executed in right screen for the disk
        """
        self.node.executeInScreen(self.screenname,cmd,env=env,session="perftest")

    def __str__(self):
        return "disk:%s"%(self.devname)

    def __repr__(self):
        return self.__str__()
