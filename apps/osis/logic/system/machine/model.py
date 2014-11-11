from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Machine(OsisBaseObject):

    """
    identifies a machine in the grid
    can be a lxc container or kvm vm or ...
    """

    def __init__(self, ddict={}):
        if ddict <> {}:
            self.load(ddict)
        else:
            self.id = 0
            self.gid = 0
            self.nid = 0
            self.name = ""
            self.roles = []
            self.netaddr = None
            self.guid = None
            self.ipaddr=[]
            self.active = True
            self.state = ""  #STARTED,STOPPED,RUNNING,FROZEN,CONFIGURED,DELETED
            self.mem=0 #in MB
            self.cpucore=0 #nr of cores cpu
            self.description=""
            self.otherid=""
            self.type = "" #KVM,LXC
            self.lastcheck=0 #epoch of last time the info was checked from reality

    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        C= "%s_%s_%s"%(self.gid,self.nid,self.name)
        return j.tools.hash.md5_string(C)

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.id = int(self.id)
        # self.sguid=struct.pack("<HHL",self.gid,self.bid,self.id)
        self.guid = "%s_%s" % (self.gid, self.id)
        self.lastcheck=j.base.time.getTimeEpoch() 
        return self.guid