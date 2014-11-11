from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Info(OsisBaseObject):

    """
    identifies a piece of info of the env
    """

    def __init__(self, ddict={},category="",content=""):
        if ddict <> {}:
            self.load(ddict)
        else:
            self.gid=j.application.whoAmI.gid
            self.nid=j.application.whoAmI.nid
            self.category=category
            self.content=""
            self.epoch=j.base.time.getTimeEpoch()
            self.getSetGuid()

    def getUniqueKey(self):
        return j.base.idgenerator.generateGUID()

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.nid = int(self.nid)
        self.guid = "%s_%s_%s" % (self.gid, self.nid,self.category)
        return self.guid
