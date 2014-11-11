from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Fake4Test(OsisBaseObject):

    """
    """

    def __init__(self, ddict={}):
        if ddict <> {}:
            self.load(ddict)
        else:
            self.id = 0
            self.gid = 0
            self.name = ""
            self.roles = []
            self.netaddr = None
            self.guid = None
            self.machineguid = ""
            self.ipaddr=[]
            self.active = True
            self.description=""

    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        return j.tools.hash.md5_string(self.name)

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.id = int(self.id)
        # self.sguid=struct.pack("<HH",self.gid,self.id)
        self.guid = "%s_%s" % (self.gid, self.id)

        return self.guid

