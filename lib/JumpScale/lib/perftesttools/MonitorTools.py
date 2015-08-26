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
