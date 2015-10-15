from JumpScale import j

from NodeBase import NodeBase
from MonitorTools import MonitorTools
from PerfTestTools import *
from MonitorTools import *
from Disk import *


class NodeNas(NodeBase):
    def __init__(self, ipaddr, sshport=22, nrdisks=0, fstype="xfs", debugdisk="", name=""):
        NodeBase.__init__(self, ipaddr=ipaddr, sshport=sshport, role="nas", name=name)

        self.debugdisk = debugdisk
        if self.debugdisk != "":
            self.debug = True
        self.disks = []
        self.nrdisks = int(nrdisks)
        self.fstype = fstype

        # self.initDisks()

        self.perftester = PerfTestTools(self)

        disks = [item.devnameshort for item in self.disks]
        self.startMonitor(disks=disks)

        self.initTest()

    def initTest(self):
        screens = []
        for i in range(self.nrdisks):
            screens.append("ptest%s" % i)
        if len(screens) > 0:
            self.prepareTmux("perftest", screens)

    def initDisks(self):

        if self.debug==False:
            diskids="bcdefghijklmnopqrstuvwxyz"
            for i in range(self.nrdisks):
                diskname="/dev/vd%s"%diskids[i]
                disk=Disk(diskname,node=self,disknr=i+1,screenname="ptest%s"%(i))
                self.disks.append(disk)

            # check mounts
            print "check disks are mounted and we find them all"
            rc, result, err = self.ssh.execute("mount")
            for line in result.split("\n"):
                if line.find(" on ") != -1 and line.startswith("/dev/v"):  # and line.find(self.fstype)!=-1:
                    # found virtual disk
                    devname = line.split(" ")[0]
                    if devname.startswith("/dev/vda"):
                        continue
                    disk = self.findDisk(devname)
                    if disk is not None:
                        disk.mounted = True
                        disk.mountpath = line.split(" on ")[1].split(" type")[0].strip()
                        disk.node = self

            for disk in self.disks:
                if disk.mounted is False:
                    disk.initDiskXFS()

                    # raise RuntimeError("Could not find all disks mounted, disk %s not mounted on %s"%(disk,self))

            print "all disks mounted"

        else:
            i = 0
            disk = Disk(self.debugdisk)
            self.disks.append(disk)
            disk.screenname = "ptest%s"%i
            disk.disknr = i+1
            disk.mountpath = "/tmp/dummyperftest/%s" % i
            j.system.fs.createDir(disk.mountpath)
            disk.node = self

    def createLoopDev(self, size, backend_file):
        """
        size : size of the disk to create in MB
        """
        # create backend file
        count = int(size) * 1000
        cmd = 'dd if=/dev/zero of=%s bs=1kB count=%d' % (backend_file, int(count))
        self.execute(cmd, env={}, dieOnError=False, report=True)

        # create loop device
        cmd = 'losetup -f %s;losetup -a' % backend_file
        rc, out, err = self.execute(cmd, env={}, dieOnError=True, report=True)
        dev = ""
        for line in out.splitlines():
            if line.find(backend_file):
                dev = line.split(':')[0]
                break
        if dev == '':
            raise RuntimeError("fail to create loop dev on %s" % backend_file)

        # add new dev to known disks
        diskNr = len(self.disks)
        disk = Disk(dev, node=self, disknr=diskNr, screenname="ptest%s" % diskNr)
        disk.mountpath = dev
        self.disks.append(disk)
        self.nrdisks += 1

        disk.initDiskXFS()

        # make sure tmux sessions exists
        self.initTest()

    def findDisk(self,devname):
        for disk in self.disks:
            if disk.devname==devname:
                return disk
        return None
