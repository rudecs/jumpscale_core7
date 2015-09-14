from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Process(OsisBaseObject):

    """
    unique process
    """

    def __init__(self, ddict={}, gid=0,aid=0,nid=0,name="",instance="",systempid=0, id=''):
        if ddict != {}:
            self.load(ddict)
            self.getSetGuid()
        else:
            self.id = 0
            self.gid = gid
            self.nid = nid
            self.aysdomain= ""
            self.aysname= ""
            self.pname = name  #process name
            self.sname= "" #name as specified in startup manager
            self.ports = []
            self.instance = instance
            if systempid!=0:
                self.systempids = [systempid]  # system process id (PID) at this point
            else:
                self.systempids=[]
            self.guid = ""
            # self.sguid = None
            self.epochstart = j.base.time.getTimeEpoch()
            self.epochstop = 0
            self.active = True
            self.lastcheck=0 #epoch of last time the info was checked from reality
            self.cmd=""
            self.workingdir=''
            self.parent=""
            self.user=""
            self.type=""
            self.statkey="" #key as used in graphite


            r=["nr_file_descriptors","nr_ctx_switches_voluntary","nr_ctx_switches_involuntary","nr_threads",\
                "cpu_time_user","cpu_time_system","cpu_percent","mem_vms","mem_rss",\
                "io_read_count","io_write_count","io_read_bytes","io_write_bytes","nr_connections_in","nr_connections_out"]
            for item in r:
                self.__dict__[item]=0.0
            self.getSetGuid()

    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        C="%s_%s_%s_%s_%s_%s_%s_%s"% (self.gid,self.nid, self.aysdomain,self.aysname,self.workingdir,self.cmd,self.pname,self.sname)
        return j.tools.hash.md5_string(C)

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.id = int(self.id)
        
        # if self.sname != "":
        #     key="%s_%s"%(self.aysdomain,self.sname)
        # else:
        #     key=self.pname

        self.guid = "%s_%s" % (self.gid, self.id)
        self.lastcheck=j.base.time.getTimeEpoch() 
        return self.guid

    def getContentKey(self):
        """
        is like returning the hash, is used to see if object changed
        """
        out=""
        for item in ["gid","nid","aysdomain","aysname","pname","sname","ports","systempids","epochstart","epochstop","active","cmd","workingdir"]:
            out+=str(self.__dict__[item])
        return j.tools.hash.md5_string(out)


        