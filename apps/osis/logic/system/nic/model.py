from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Nic(OsisBaseObject):

    """
    identifies a nic in the grid
    """

    def __init__(self, ddict={}):
        if ddict <> {}:
            self.load(ddict)
        else:
            self.id = 0
            self.gid = 0
            self.nid = 0
            self.name = ""
            self.mac = ""
            self.guid = None
            self.ipaddr=[]
            self.active = False
            self.lastcheck=0 #epoch of last time the info was checked from reality

            for item in ["kbytes_sent","kbytes_recv","packets_sent","packets_recv","errin","errout","dropin","dropout"]:
                self.__dict__[item]=0

    def getContentKey(self):
        C="%s_%s_%s_%s_%s_%s_%s"%(self.gid,self.nid,self.id,self.name,self.mac,self.ipaddr,self.active)
        return j.tools.hash.md5_string(C)


    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        C="%s_%s_%s"%(self.gid,self.nid,self.name)
        return j.tools.hash.md5_string(C)


    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.nid = int(self.nid)
        self.id = int(self.id)

        self.guid = "%s_%s_%s" % (self.gid,self.nid,self.id)
        self.lastcheck=j.base.time.getTimeEpoch() 

        return self.guid

