from JumpScale import j

import statsd
import sys
import time
import json
import os
import psutil
from JumpScale.lib.perftesttools import InfluxDumper


class MonitorClient():
    def __init__(self):
        luapath="stat.lua"
        lua=j.system.fs.fileGetContents(luapath)
        self._sha=self.redis.script_load(lua)       

    # def reset(self):
    #     import ipdb
    #     ipdb.set_trace()
        
    #     self.redis.delete("stats")
    #     self.redis.delete("queues:stats")

    def measure(self,key,measurement,tags,value,type="A",aggrkey=""):
        """
        @param tags node:kds dim:iops location:elgouna
        """
        now=int(time.time()*1000)

        res = self.redis.evalsha(self._sha,1,key,measurement,value,str(now),type,tags,self.nodename)

        #LETS NOT DO TOTAL FOR NOW
        # if aggrkey!="":
        #     tags=j.core.tags.getObject(tags)
        #     try:
        #         tags.tagDelete("node")
        #     except:
        #         pass
        #     try:
        #         tags.tagDelete("disk")
        #     except:
        #         pass            
        #     tags.tagSet("node","total")
        #     res= self.redis.evalsha(self._sha,1,aggrkey,measurement,value,str(now),type,tags,"total")   

        print "%s %s"%(key,res)

        return res

    def measureDiff(self,key,measurement,tags,value,aggrkey=""):
        return self.measure(key,measurement,tags,value,type="D",aggrkey=aggrkey)


class MonitorTools(MonitorClient):

    def __init__(self,redis,nodename,tags=""):
        self.redis=redis
        self.nodename=nodename
        self.tags=tags
        MonitorClient.__init__(self)


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

        tags="disk:%s node:%s %s"%(dev,self.nodename,self.tags)

        measurement=["readios","iops_r"]
        key="%s.%s.%s"%(self.nodename,dev,measurement[1])        
        val=int(int(data[measurement[0]])/8)
        readiops=self.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        measurement=["writeios","iops_w"]
        key="%s.%s.%s"%(self.nodename,dev,measurement[1])        
        val=int(int(data[measurement[0]])/8)
        writeiops=self.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        measurement="kbsec_w"
        key="%s.%s.%s"%(self.nodename,dev,measurement)        
        kbsecw=int(int(data["writeios"])*4/1024)
        kbsecw=self.measureDiff(key,measurement,tags,kbsecw,aggrkey=measurement)

        measurement="kbsec_r"
        key="%s.%s.%s"%(self.nodename,dev,measurement)        
        kbsecr=int(int(data["readios"])*4/1024)
        kbsecr=self.measureDiff(key,measurement,tags,kbsecr,aggrkey=measurement)

        measurement="kbsec"
        key="%s.%s.%s"%(self.nodename,dev,measurement)        
        kbsec=int(int(data["readios"])*512/1024)+int(int(data["writeios"])*512/1024)
        kbsec=self.measureDiff(key,measurement,tags,kbsec,aggrkey=measurement)

        measurement="iops"   
        key="%s.%s.%s"%(self.nodename,dev,measurement)        
        iops=int(int(data["readios"])/8)+int(int(data["writeios"])/8)
        iops=self.measureDiff(key,measurement,tags,iops,aggrkey=measurement)

        measurement=["readticks","readticks"]
        key="%s.%s.%s"%(self.nodename,dev,measurement[1])        
        val=int(data[measurement[0]])
        readticks=self.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        measurement=["writeticks","writeticks"]
        key="%s.%s.%s"%(self.nodename,dev,measurement[1])        
        val=int(data[measurement[0]])
        writeticks=self.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        measurement=["inflight","inflight"]
        key="%s.%s.%s"%(self.nodename,dev,measurement[1])        
        val=int(data[measurement[0]])
        inflight=self.measureDiff(key,measurement[1],tags,val,aggrkey=measurement[1])

        print "%s: iops:%s mb/sec:%s (R:%s/W:%s)"%(dev,iops,round(kbsec/1024,1),round(kbsecr/1024,1),round(kbsecw/1024,1))

    def cpustat(self):
        tags="node:%s %s"%(self.nodename,self.tags)
        
        val=int(psutil.cpu_percent())
        measurement="cpu_perc"
        key="%s.%s"%(self.nodename,measurement)      
        self.measure(key,measurement,tags,val,aggrkey=measurement)

        val=int(psutil.avail_phymem()/1024/1024)
        measurement="mem_free_mb"
        key="%s.%s"%(self.nodename,measurement)
        self.measure(key,measurement,tags,val,aggrkey=measurement)

        val=int(psutil.virtmem_usage()[3])
        measurement="mem_virt_perc"
        key="%s.%s"%(self.nodename,measurement)
        self.measure(key,measurement,tags,val,aggrkey=measurement)

        val=int(psutil.phymem_usage()[2])
        measurement="mem_phy_perc"
        key="%s.%s"%(self.nodename,measurement)
        self.measure(key,measurement,tags,val,aggrkey=measurement)
       
        res=psutil.cpu_times_percent()        
        names=["cputimeperc_user","cputimeperc_nice","cputimeperc_system","cputimeperc_idle","cputimeperc_iowait","cputimeperc_irq","cputimeperc_softirq","steal","guest","guest_nice"]
        for i in range(len(names)):
            if names[i].startswith("cputime"):
                val=int(res[i])
                measurement=names[i]
                key="%s.%s"%(self.nodename,measurement)
                self.measure(key,measurement,tags,val,aggrkey=measurement)

        
    def netstat(self):
        tags="node:%s %s"%(self.nodename,self.tags)
        names=["kbsend","kbrecv","psent","precv","errin","errout","dropin","dropout"]
        res=psutil.net_io_counters()
        for i in range(len(names)):
            if names[i] in ["kbsend","kbrecv"]:
                val=int(res[i])/1024                
            else:
                val=int(res[i])
            measurement=names[i]
            key="%s.%s"%(self.nodename,measurement)
            self.measureDiff(key,measurement,tags,val,aggrkey=measurement)
            

    def startMonitorLocal(self,disks=[],cpu=False,network=False):
        count=6
        while True:
            # cmd="iostat -m"
            # j.do.executeInteractive(cmd)
            if disks!=[]:
                for dev in disks:
                    self.diskstat(dev)
            if cpu:
                self.cpustat()                

            if network:
                if count>5:
                    self.netstat()  
                    count=0
                else:
                    count+=1

            time.sleep(2)
