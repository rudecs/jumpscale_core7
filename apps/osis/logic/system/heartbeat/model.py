from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class heartbeat(OsisBaseObject):

    """
    """
    def __init__(self,ddict={}):
        if ddict != {}:
            self.load(ddict)
        else:
            self.nid=j.application.whoAmI.nid
            self.gid=j.application.whoAmI.gid
            self.lastcheck=j.base.time.getTimeEpoch()
            self.getSetGuid()

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.guid = "%s_%s" % (self.gid, self.nid)
        return self.guid
