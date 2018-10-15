from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Grid(OsisBaseObject):

    """
    identifies the grid
    """

    def __init__(self, ddict={}, name="", id=0, useavahi=1, settings=None):
        if ddict != {}:
            self.load(ddict)
        else:
            self.name = name
            self.useavahi = useavahi
            self.nid=0
            self.id=id
            self.settings = settings or {}
            self.guid=id

    def initFromLocalNodeInfo(self):
        """
        get ipaddr info & gid & nid from local config
        """
        self.ipaddr=[item for item in j.system.net.getIpAddresses() if item !="127.0.0.1"]
        self.id = j.application.whoAmI.gid
        self.nid = j.application.whoAmI.nid

    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        return self.id

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.guid = int(self.id)
        self.id = int(self.id)
        return self.guid
