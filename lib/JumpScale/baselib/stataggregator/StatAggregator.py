from JumpScale import j
import JumpScale.baselib.redis

import time

class Stat():
    def __init__(self,period=3600,memonly=False,percent=False):
        self._type = 'Stat'
        self.results={}
        self.result=0
        self.period=period
        self.memonly=memonly
        self.percent=percent

    def set(self,now,val,remember=True):        
        if self.percent:
            self.result=val
        else:
            self.result=int(round(val,0))
        if remember:
            self.results[now]=self.result
        else:
            self.results[0]=self.result            
        return self.result

    def dump(self):
        return self.__dict__

    def load(self, data):
        self.__dict__ = data

    def getAvgMax(self):
        """
        @return (avg,max)
        """
        tot=0.0
        nr=0
        m=0 #max
        for key in list(self.results.keys()):
            tot+=self.results[key]
            nr+=1
            if self.results[key]>m:
                m=self.results[key]
        if nr != 0:
            if self.percent:
                return (round(tot/nr,2),m)
            else:
                return (int(round(tot/nr,0)),m)
        else:
            return [0,0]

    def clean(self,now):
        for key in list(self.results.keys()):
            if key<now-self.period:
                self.results.pop(key)

class StatDiffPerSec(Stat):
    def __init__(self,period=3600,memonly=False,percent=False):
        Stat.__init__(self,period,memonly=memonly)
        self._type = 'StatDiffPerSec'
        self.lastPoll=0
        self.lastVal=0
        self.percent=percent

    def set(self,now,val,remember=True):        
        if self.lastPoll==0:
            result=0
        else:
            period=now-self.lastPoll
            if period>7200:
                # raise RuntimeError("period for stat since last poll should never be more than 2h")
                return
            if self.percent:
                result=round((val-self.lastVal)/float(period),2)
            else:
                result=int(round((val-self.lastVal)/float(period),0))

        self.lastPoll=now
        self.lastVal=val
        self.result=result
        if remember:
            self.results[now]=result
        else:
            self.results[0]=result
     
        return result

    def getAvgMax(self):
        """
        @return (avg,max)
        """
        tot=0.0
        nr=0
        m=0 #max
        for key in list(self.results.keys()):
            if self.results[key]>0:
                tot+=self.results[key]
                nr+=1
            if self.results[key]>m:
                m=self.results[key]
        if nr != 0:
            if self.percent:
                return (round(tot/nr,2),m)
            else:
                return (int(round(tot/nr,0)),m)
        else:
            return [0,0]
                

class StatAggregator():

    def __init__(self):
        redis = j.clients.redis.getRedisClient('127.0.0.1', 9999)
        self.stats = redis.getDict("stataggregator")
        self.log=False
        if self.log:
            self.logdir=j.system.fs.joinPaths(j.dirs.logDir,"stats_aggregator")
            self.logdirCarbon=j.system.fs.joinPaths(j.dirs.logDir,"stats_carbon")


    def getTime(self):
        return time.time()

    def send2log(self,name,key,val):
        if self.log:
            splitted=key.split(".")
            if len(splitted)>2:
                splitted0=splitted[:-2]
                splitted1=splitted[:-1]
            elif len(splitted)>1:
                splitted0=splitted[:-1]
                splitted1=[]
            else:
                raise RuntimeError("key needs to have at least 1 '.'")

            path=j.system.fs.joinPaths(j.dirs.logDir,name,"/".join(splitted0))
            path2=j.system.fs.joinPaths(j.dirs.logDir,name,"/".join(splitted1))
            
            if not j.system.fs.exists(path=path):
                j.system.fs.createDir(path)
            if j.system.fs.isDir(path2):
                path2=j.system.fs.joinPaths(path2,splitted1[-1])

            path2="%s_%s"%(path2,j.base.time.getDayId())

            j.system.fs.writeFile(path2,"%s %-100s %s\n"%(self.getTime(),key,val),True)
               
    def loadStat(self, key=None, data=None):
        if key is not None:
            data = self.stats[key]
        if data['_type'] == 'Stat':
            stat = Stat()
        else:
            stat = StatDiffPerSec()
        stat.load(data)
        return stat

    def set(self,key,val,ttype="N",remember=True,memonly=False,percent=False):
        val=float(val)
        if key not in self.stats:
            stat = self.registerStats(key,ttype,memonly,percent=percent)
        else:
            stat = self.loadStat(key)
        result = stat.set(self.getTime(),val,remember=remember)
        self.stats[key] = stat.dump()
        self.send2log("stats_aggregator",key,val)
        
        # print "set:%s:%s result:%s"%(key,val,result)
        return result

    def get(self,key):
        if key not in self.stats:
            raise RuntimeError("Could not find stat with key:%s"%key)
        return self.loadStat(key).result

    def getAvgMax(self,key):
        if key not in self.stats:
            raise RuntimeError("Could not find stat with key:%s"%key)
        return self.loadStat(key).getAvgMax()

    def registerStats(self,key,ttype="N",memonly=False,percent=False):
        """
        type is N or D (D from diff)
        """

        if ttype=="N":
            stat = Stat(memonly=memonly,percent=percent)
        else:            
            stat = StatDiffPerSec(memonly=memonly,percent=percent)
        self.stats[key] = stat.dump()
        return stat

    def clean(self):
        for key in self.stats:
            stat=self.loadStat(key)
            stat.clean(self.getTime())

    def delete(self,prefix):
        for key in list(self.stats.keys()):
            if key.startswith(prefix):
                self.stats.pop(key)
                print(("DELETE:%s"%key))
                

    def list(self,prefix="",memonly=False,avgmax=False):
        result={}
        for key in list(self.stats.keys()):
            stat=self.loadStat(key)
            if prefix=="" or key.startswith(prefix):
                if memonly==None or stat.memonly==memonly:
                    if "lastPoll" in stat.__dict__:
                        ttype="D"
                    else:
                        ttype="N"
                    if avgmax:
                        a,m=stat.getAvgMax()
                        result[key]=[ttype,stat.result,a,m]
                    else:
                        result[key]=[ttype,stat.result]
        return result

    def send2carbon(self):
        out=""
        for key in list(self.stats.keys()):
            stat=self.stats[key]
            if stat.memonly:
                # print "MEMONLY:%s"%key
                continue
            #out+="%s.last %s\n" %(key,stat.result)
            avg,m=stat.getAvgMax()
            out+="%s %s\n" %(key,avg)
            #out+="%s.max %s\n" %(key,m)
            #self.send2log("stats_carbon","%s.last"%key,stat.result)
            self.send2log("stats_carbon","%s"%key,avg)
            #self.send2log("stats_carbon","%s.max"%key,m)
        j.clients.graphite.send(out)






