from JumpScale import j


from _MonObjectBaseFactory import *

class ProcessObjectFactory(MonObjectBaseFactory):
    def __init__(self,host,classs):
        MonObjectBaseFactory.__init__(self,host,classs)
        self.osis=j.clients.osis.getCategory(self.host.daemon.osis,"system","process")
        #@todo P1 load them from ES at start (otherwise delete will not work), make sure they are proper osis objects
        j.core.processmanager.childrenPidsFound={}
        self.pid2name={}


    def getProcessStatProps(self):
        r=["nr_file_descriptors","nr_ctx_switches_voluntary","nr_ctx_switches_involuntary","nr_threads",\
                "cpu_time_user","cpu_time_system","cpu_percent","mem_vms","mem_rss",\
                "io_read_count","io_write_count","io_read_bytes","io_write_bytes","nr_connections_out","nr_connections_in"]
        return r

    def getFromSystemPid(self,pid):
        for key,obj in self.monitorobjects.iteritems():
            if pid in obj.db.systempids:
                return obj
        return None

class ProcessObject(MonObjectBase):

    def __init__(self,cache):
        self._expire=10 #means after 5 sec the cache will create new one
        MonObjectBase.__init__(self,cache)
        self.p=None #is process object
        self.children=[]        

        self.netConnectionsIn=[]
        self.netConnectionsOut=[]


    def getStatInfo(self,totals=False):
        """
        @format dict or txt
        """
        result={}
        if totals:
            self.getTotalsChildren()

        for name in j.core.processmanager.monObjects.processobject.getProcessStatProps(totals):
            result[name]=self.db.__dict__[name]

        return result


    def getTotalsChildren(self):
        """
        calculate total for children
        """
        for item in j.core.processmanager.monObjects.processobject.getProcessStatProps():
            for child in self.children:
                self.db.__dict__[item]+=float(child.db.__dict__[item])            

    def __repr__(self):
        sp=",".join([str(item) for item in self.db.systempids])            
        return "%-25s:%-25s:%s" %(self.db.pname,self.db.sname,sp)

    def repr(self):
        out=""
        for key,val in self.__dict__.iteritems():
            if key not in ["p","children","db"]:
                out+="%s:%s\n"%(key,val)
        for key,val in self.db.__dict__.iteritems():
            out+="%s:%s\n"%(key,val)

        items=out.split("\n")
        items.sort()
        return "\n".join(items)


    __str__ = __repr__

