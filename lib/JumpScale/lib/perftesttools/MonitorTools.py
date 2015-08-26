from JumpScale import j

import statsd
import sys
import time
import json
import os
import psutil

class MonitorClient():
    def __init__(self,redis,nodename):
        self.r=redis
        luapath="stat.lua"
        lua=j.system.fs.fileGetContents(luapath)
        self._sha=self.r.script_load(lua)
        self.nodename=nodename

    def reset(self):
        self.r.delete("stats:total")
        self.r.delete("stats:sda")
        self.r.delete("queues:stats")


    def measure(self,key,measurement,tags,value,type="A",aggrkey=""):
        """
        @param tags node:kds dim:iops location:elgouna
        """
        now=int(time.time()*1000)

        res = self.r.evalsha(self._sha,1,key,measurement,value,str(now),type,tags,self.nodename)

        if aggrkey!="":
            tags=j.core.tags.getObject(tags)
            try:
                tags.tagDelete("node")
            except:
                pass
            try:
                tags.tagDelete("disk")
            except:
                pass            
            tags.tagSet("node","total")
            res= self.r.evalsha(self._sha,1,aggrkey,measurement,value,str(now),type,tags,"total")             

        return res

    def measureDiff(self,key,measurement,tags,value,aggrkey=""):
        return self.measure(key,measurement,tags,value,type="D",aggrkey=aggrkey)


class MonitorTools():

    def __init__(self,redis,node):
        self.redis=redis
        self.node=nodename
        self.monitorclient=MonitorClient(redis,node.name)


    def diskstat(self,dev="sda"):
        """
        read I/Os       requests      number of read I/Os processed (512 bytes)
        read merges     requests      number of read I/Os merged with in-queue I/O
        read sectors    sectors       number of sectors read
        read ticks      milliseconds  total wait time for read requests
        write I/Os      requests      number of write I/Os processed
        write merges    requests      number of write I/Os merged with in-queue I/O
        write sectors   sectors       number of sectors written
        write ticks     milliseconds  total wait time for write requests
        in_flight       requests      number of I/Os currently in flight
        io_ticks        milliseconds  total time this block device has been active
        time_in_queue   milliseconds  total wait time for all requests
        """
        path="/sys/block/%s/stat"%dev
        lines = open(path, 'r').readlines()
        split=lines[0].split()
        columns=["readios","readmerges","readsectors","readticks","writeios","writemerges","writesectors","writeticks","inflight","ioticks","timeinqueue"]
        data = dict(zip(columns, split))
        print data

        tags="disk:%s node:%s %s"%(dev,self.monitor.nodename,self.tags)

        measurement=["readios","iops_r"]
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement[1])        
        val=int(int(data[measurement[0]])/8)
        readiops=self.monitor.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        measurement=["writeios","iops_w"]
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement[1])        
        val=int(int(data[measurement[0]])/8)
        writeiops=self.monitor.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        measurement="kbsec_w"
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement)        
        kbsecw=int(int(data["writeios"])*4/1024)
        kbsecw=self.monitor.measureDiff(key,measurement,tags,kbsecw,aggrkey=measurement)

        measurement="kbsec_r"
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement)        
        kbsecr=int(int(data["readios"])*4/1024)
        kbsecr=self.monitor.measureDiff(key,measurement,tags,kbsecr,aggrkey=measurement)

        measurement="kbsec"
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement)        
        kbsec=int(int(data["readios"])*512/1024)+int(int(data["writeios"])*512/1024)
        kbsec=self.monitor.measureDiff(key,measurement,tags,kbsec,aggrkey=measurement)

        measurement="iops"   
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement)        
        iops=int(int(data["readios"])/8)+int(int(data["writeios"])/8)
        iops=self.monitor.measureDiff(key,measurement,tags,iops,aggrkey=measurement)

        measurement=["readticks","readticks"]
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement[1])        
        val=int(data[measurement[0]])
        readticks=self.monitor.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        measurement=["writeticks","writeticks"]
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement[1])        
        val=int(data[measurement[0]])
        writeticks=self.monitor.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        measurement=["inflight","inflight"]
        key="%s.%s.%s"%(self.monitor.nodename,dev,measurement[1])        
        val=int(data[measurement[0]])
        inflight=self.monitor.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        print "%s: iops:%s mb/sec:%s (R:%s/W:%s)"%(dev,iops,round(kbsec/1024,1),round(kbsecr/1024,1),round(kbsecw/1024,1))

    def cpustat(self):
        from IPython import embed
        print "DEBUG NOW cpustat"
        embed()
        

    def startMonitorLocal(self,disks=False,cpu=False,network=False):
        while True:
            # cmd="iostat -m"
            # j.do.executeInteractive(cmd)
            if disks:
                for dev in self.disks:
                    self.diskstat(dev)
            if cpu:
                self.cpustat()                

                # print r
                # self.stats.set("test",10)
            time.sleep(2)

class PerformanceTesterTools():
    def __init__(self):
        pass

    def sequentialWriteReadBigBlock(self,node,disknr,nrfiles=1):
        """
        disknr starts with 1
        """
        if disknr<1:
            raise RuntimeError("disknr starts with 1")
        disk=node.disks[disknr-1]        
        print "SEQUENTIAL WRITE %s %s"%(node,disk)
        
        path="%s/testfile"%disk.mountpath
        filepaths=""
        for i in range(nrfiles+1):
            filepaths+="-F '%s%s' "%(path,(i))

        cmd="iozone -i 0 -i 1 -R -s 1000M -I -k -l 5 -O -r 256k -t %s -T %s"%(nrfiles,filepaths)
        disk.execute(cmd)

class Disk():
    def __init__(self,devname,node=None):
        self.devname=devname
        self.devnameshort=self.devname.split("/")[2]
        self.mounted=False
        self.mountpath=None
        self.node=node
        self.disknr=None

    def initDiskXFS(self):
        print "initxfs:%s"%self
        res=self.node.ssh.execute("lsblk -f |grep %s"%self.devnameshort, dieOnError=False)[1].strip()
        if res=="":
            #did not find formatted disk
            self.node.ssh.execute("mkfs.xfs -f /dev/vdb")
        elif res.find("xfs")==-1:
            #did find but no xfs
            self.node.ssh.execute("mkfs.xfs -f /dev/vdb")
        self.node.ssh.execute("mkdir -p /storage/%s"%self.disknr)
        self.node.ssh.execute("mount %s /storage/%s"%(self.devname,self.disknr), dieOnError=False)
        print "initxfs:%s check mount"%self
        if not self.checkMount():
            raise RuntimeError("could not mount %s"%self)
        print "initxfs:%s done"%self

    def checkMount(self):
        rc,result,err=self.node.ssh.execute("mount")
        for line in result.split("\n"):
            if line.find(" on ")!=-1 and line.startswith(self.devname) and line.find(self.node.fstype)!=-1:
                return True
        return False

    def execute(self,cmd):
        """
        gets executed in right screen for the disk
        """
        cmd2="tmux send-keys -t '%s' '%s\n'"%(self.screenname,cmd)
        print "execute:'%s' on %s %s"%(cmd,self.node,self)
        self.node.execute(cmd2)

    def __str__(self):
        return "disk:%s"%(self.devname)

    def __repr__(self):
        return self.__str__()

class NodeBase():
    def __init__(self,ipaddr,sshport=22,nrdisks=0,role=None,fstype="xfs"):
        """
        existing roles
        - vnas
        - monitor
        - host
        - debug (a local host on which we run all)

        """
        self.ipaddr=ipaddr
        self.disks=[]
        self.nrdisks=nrdisks
        self.fstype=fstype
        self.ismaster=False
        self.ishost=False
        self.perftester=PerformanceTesterTools()

        self.ssh=j.remote.ssh.getSSHClientUsingSSHAgent(host=ipaddr, username='root', port=sshport, timeout=10)
        # self.sal=j.ssh.unix.get(self.ssh)
        self.role=role
        self.tmuxinit()

        self.initDisksRemote()

    def initDisksRemote(self):
        if self.role=="vnas":
            if testpaths==[] and self.nrdisks>0:
                diskids="bcdefghijklmnopqrstuvwxyz"
                for i in range(self.nrdisks+1):
                    diskname="/dev/vd%s"%diskids[i]
                    disk=Disk(diskname,node=self)
                    self.disks.append(disk)            
                    disk.screenname="ptest%s"%(i+1)
                    disk.disknr=i+1

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
        self.ssh.execute("tmux new-window -t 'perftest' -n 'monitor'") 
        self.ssh.execute("tmux new-window -t 'perftest' -n 'iostat'")  
       
        self.executeInScreen("iostat","apt-get install iotools;iostat -c -d 1")  

    def startMonitorRemote(self):
        mypath=os.path.realpath(__file__)
        luapath=j.system.fs.joinPaths(j.system.fs.getDirName(mypath),"stat.lua")
        ftp=self.ssh.getSFtpConnection()
        ftp.put(mypath,"/tmp/perftest.py")
        ftp.put(luapath,"/tmp/stat.lua")
        self.executeInScreen("monitor","cd /tmp;python perftest.py monitor")    
        
    def execute(self,cmd, dieOnError=False):
        self.ssh.execute(cmd, dieOnError=dieOnError)

    def executeInScreen(self,screenname,cmd):
        """
        gets executed in right screen for the disk
        """
        cmd2="tmux send-keys -t '%s' '%s\n'"%(screenname,cmd)
        print "execute:'%s' on %s in screen:%s"%(cmd,self,screenname)
        self.execute(cmd2)
        
    def findDisk(self,devname):
        for disk in self.disks:
            if disk.devname==devname:
                return disk
        raise RuntimeError("cannot find disk:%s"%devname)

    def __str__(self):
        return "node:%s"%self.ipaddr

    def __repr__(self):
        return self.__str__()

class NodeHost(NodeBase,MonitoringTools):
    def __init__(self,ipaddr,sshport=22,redis=None): 
        """
        is host running the hypervisor
        """
        self.ismaster=False
        self.ishost=True
        self.redis=redis
        Node.__init__(self,ipaddr=ipaddr,sshport=sshport,nrdisks=0,testpaths=[])

    def startRedis2Influxdb(self):  
        mypath=os.path.realpath(__file__)
        luapath=j.system.fs.joinPaths(j.system.fs.getDirName(mypath),"stat.lua")
        ftp=self.ssh.getSFtpConnection()
        ftp.put(mypath,"/tmp/perftest.py")
        ftp.put(luapath,"/tmp/stat.lua")
        self.executeInScreen("monitor","cd /tmp;python perftest.py monitor")    

    def tmuxinit(self):
        # self.ssh.execute("tmux kill-session -t mgmt", dieOnError=False)
        self.ssh.execute("tmux new-session -d -s monitor -n monitor", dieOnError=False)
        mypath=os.path.realpath(__file__)
        luapath=j.system.fs.joinPaths(j.system.fs.getDirName(mypath),"stat.lua")
        j.system.fs.writeFile("/tmp/key",self.key)
        print "push monitoring of physical node underneith hypervisor"
        ftp=self.ssh.getSFtpConnection()
        ftp.put(mypath,"/tmp/perftest.py")
        self.executeInScreen("monitor","cd /tmp;python perftest.py monitorhost")    
        print "monitoring on %s running"%self

class NodeMaster(NodeBase,MonitoringTools):
    def __init__(self,ipaddr,sshport=22,redis=None,remote=False,key=""): 
        self.ismaster=True   
        self.redis=redis
        self.remote=remote
        self.key=key
        Node.__init__(self,ipaddr=ipaddr,sshport=sshport,nrdisks=0,testpaths=[])

    def startRedis2Influxdb(self):  
        mypath=os.path.realpath(__file__)
        ftp=self.ssh.getSFtpConnection()
        ftp.put(mypath,"/tmp/perftest.py")
        self.executeInScreen("dumper","cd /tmp;python perftest.py dbpopulate")  

    def tmuxinit(self):
        if self.remote:
            # self.ssh.execute("tmux kill-session -t mgmt", dieOnError=False)
            self.ssh.execute("tmux new-session -d -s mgmt -n mgmt", dieOnError=False)
            self._runRemote()
        else:
            self.ssh.execute("tmux kill-session -t dumper", dieOnError=False)
            self.ssh.execute("tmux new-session -d -s dumper -n dumper")

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

#HOW TO USE
howtouse="""
- python perftest.py monitor
  will capture information from system & send to local redis
  redis will aggregate and build a queues
  no need to do this manually

- python perftest.py dbpopulate
  will read the queue from redis & put stats in influxdb
  no need to do this manually

- python perftest.py
  will start the performance test & generate stats
  the perftest will make sure monitor & dbpopulate is being launched

"""

hostname="kds"
redis= j.clients.redis.getByInstance('system')

if len(sys.argv)>1:
    # redis=j.clients.credis.getRedisClient("localhost",9999)
    
    masterInDemo1="192.168.103.252"

    if sys.argv[1]=="monitor":
        m=MonitorClient(redis,nodename=hostname)
        m.reset()
        dm=PerfMonitorLocal(monitor=m,disks=["sda"])
        dm.start()
    elif sys.argv[1]=="monitorhost":
        m=MonitorClient(redis,nodename=hostname)
        dm=PerfMonitorLocal(monitor=m)
        dm.start(disks=False)        
    elif sys.argv[1]=="dbpopulate":
        redis=j.clients.redis.getRedisClient(masterInDemo1,9999)
        i=InfluxDumper(redis=redis,server="localhost",port=8086)
        i.start()
    elif sys.argv[1]=="remote":
        print "connect to master"
        nodemaster=NodeMaster("10.101.135.139",sshport=1500,redis=None,remote=True)  
else:
    #the main driver of the test script
    # node1=Node("10.101.135.139",1504,nrdisks=9)
    # 
    
    # nodemaster.startRedis2Influxdb() #make sure that script which pushes content in influxdb is started
    
    #    


    # pt=PerformanceTester()

    #test local on 1 disk with 1 thread
    # pt.sequentialWriteReadBigBlock(node=node1,disknr=1,nrfiles=1)
    # node1.startMonitor()
    # nodemaster.loopPrintStatus()

    def singleLocalNodeTest():
        nodemaster=NodeMaster("127.0.0.1",redis=redis)  
        node1=Node("127.0.0.1",22,testpaths=["/var/1"]) 
        nodemaster.startRedis2Influxdb() #make sure that script which pushes content in influxdb is started
        node1.startMonitor()
        nodehost=Node("127.0.0.1",22) 
        pt=PerformanceTester()
        pt.sequentialWriteReadBigBlock(node=node1,disknr=1,nrfiles=3)


    def multiNodeMultDiskStripTest():

        """
        if you want to work from the monitoring vm: (remote option)
        on monitoring vm do, to make sure there are keys & ssh-agent is loaded
            js 'j.do.loadSSHAgent(createkeys=True)'
            #now logout & back login into that node, this only needs to happen once

        """
        mgmtkey="""
-----BEGIN DSA PRIVATE KEY-----
MIIBuwIBAAKBgQCUsI1t6Hxvgbhi+2iXEMa3a5IlVv9AQmdqzywo63KlJklRBV8B
sS/H0QaYE6msIQOucddUf3pxNCcI0YzXIc68ViQJ/N20tLKtKn1Cs+FAQG5HgAaB
tMqIEbODwEuQoz2sM7LETxxfyKHSpq+04eu10b8AQvBqbdonxkWXojtd8wIVAOab
J9nUbkvZvMxSnbn6CANzxtqrAoGAXsNJgp6RmDDgKu8Rw0I3Be75Sgu0fMXbmCCk
35lrmjAfpRyGrGoq6t2Xjsss/lznjJSr3TIEw4amSyIVBYooKsIcryFieCc3f9um
GmBNG6Rl8PMVjfLrvKB7uONdWsmKm/pUKOdTl8aQzp+ggEsi4od5zT3UCV9voFvj
/0MxewACgYA7oh7Z3OTmIPrvdoJDtYr3EjLmck6ohmO/EdljNLNVy1A8WiLau7rH
8WmgASC9ZKOt/+Y0DqIyJSnOZHy071yPoeIU1vSQ3UcWqeKjCWJvt+3mEAHof/Ol
DeKKIzr8KKGcUPROIQmy6fooeN4idnrtI9c2QXBNYHWqekHDuTpWZAIVAIaQPzv8
Ha5/w/N6XfqnrkCeqJ2i
-----END DSA PRIVATE KEY-----        
"""
        print "init nodemaster"
        nrdisks=6

        # nodemaster=NodeMaster("10.101.135.139",sshport=1500,redis=redis,key=mgmtkey)  
        nodemaster=NodeMaster("localhost",sshport=22,redis=redis,key=mgmtkey)  
        print "start redisdumper"
        nodemaster.startRedis2Influxdb() #make sure that script which pushes content in influxdb is started
        print "start performance tester class"
        pt=PerformanceTester()
        nodesObj=[]
        nodes=["192.168.103.240","192.168.103.239","192.168.103.238","192.168.103.237"]

        for i in range(4):
            # node=Node("10.101.135.139",sshport=1501+i,nrdisks=6)
            node=Node(nodes[i],sshport=22,nrdisks=nrdisks)
            node.startMonitor()
            nodesObj.append(node)

        for i in range(4):
            node=nodesObj[i]
            print "start loadtest on %s"%node
            for diski in range(nrdisks):
                pt.sequentialWriteReadBigBlock(node=node,disknr=diski+1,nrfiles=3)
            node.startMonitor()

    # multiNodeMultDiskStripTest()
    singleLocalNodeTest()
