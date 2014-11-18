from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class VDisk(OsisBaseObject):

    """
    identifies a disk in the grid
    """

    def __init__(self, ddict={}):
        if ddict != {}:
            self.load(ddict)
        else:
            self.id = 0
            self.guid = None
            self.gid = 0
            self.nid = 0
            self.path = ""
            self.backingpath = ""
            self.size = 0 #KB
            self.free = 0 #KB
            self.sizeondisk = 0 #size on physical disk after e.g. compression ... KB
            self.fs=""
            self.active = True
            self.description=""
            self.role=""  #BOOT,DATA,...
            self.machineid=0  #who is using it
            self.order=0
            self.type="" #QCOW2,FS
            self.backup=False
            self.backuptime=0
            self.expiration=0
            self.backuplocation="" #where is backup stored (tag based notation)
            self.devicename=""
            self.lastcheck=0 #epoch of last time the info was checked from reality

        
    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        C="%s_%s_%s_%s_%s_%s"%(self.gid,self.nid,self.path,self.backup,self.type,self.backuplocation)
        return j.tools.hash.md5_string(C)

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.id = int(self.id)
        self.guid = "%s_%s" % (self.gid, self.id)
        self.lastcheck=j.base.time.getTimeEpoch() 
        return self.guid

