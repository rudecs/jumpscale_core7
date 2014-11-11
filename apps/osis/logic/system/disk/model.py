from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Disk(OsisBaseObject):

    """
    identifies a disk in the grid
    """

    def __init__(self, ddict={}):
        if ddict <> {}:
            self.load(ddict)
        else:
            self.id = 0
            self.partnr = 0
            self.gid = 0
            self.nid = 0
            self.path = ""
            self.size = 0 #KB
            self.free = 0 #KB
            self.ssd=False
            self.fs=""
            self.mounted=False
            self.mountpoint=""
            self.guid = None
            self.active = True
            self.model=""
            self.description=""
            self.type=[]  #BOOT,DATA,...
            self.lastcheck=0 #epoch of last time the info was checked from reality
        self.getSetGuid()

    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        C="%s_%s_%s_%s"%(self.gid,self.nid,self.path,self.ssd)
        return j.tools.hash.md5_string(C)

    def getContentKey(self):
        C="%s_%s_%s_%s_%s_%s_%s_%s_%s_%s"%(self.gid,self.nid,self.path,self.ssd,self.model,self.free,self.size,self.mountpoint,self.mounted,self.partnr)
        return j.tools.hash.md5_string(C)

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.guid = "%s_%s_%s" % (self.gid, self.nid, self.id)
        # if self.path.startswith('/dev/') and self.path.count('/') == 2:
        #     self.guid = "%s_%s_%s" % (self.gid, self.nid, self.path[5:])
        # else:
        #     self.guid = "%s_%s_%s" % (self.gid, self.nid, j.tools.hash.md5_string(self.path))
        self.lastcheck=j.base.time.getTimeEpoch()
        return self.guid

