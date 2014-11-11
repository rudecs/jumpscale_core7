from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Grid(OsisBaseObject):

    """
    identifies the grid
    """

    def __init__(self, ddict={}, name="", id=0, useavahi=1):
        if ddict <> {}:
            self.load(ddict)
        else:
            self.name = name
            self.useavahi = useavahi
            self.nid=0
            self.id=id
            self.guid=id            

    def initFromLocalNodeInfo(self):
        """
        get ipaddr info & gid & nid from local config
        """
        self.ipaddr=[item for item in j.system.net.getIpAddresses() if item <>"127.0.0.1"]
        self.id= j.application.config.getInt("gridmaster.grid.id")

        if not j.application.config.exists("grid.node.id"):
            #register the own masternode to the grid
            jp=j.packages.findNewest("jumpscale","grid_node")
            jp.configure()
            if j.application.config.getInt("grid.node.id")==0:
                raise RuntimeError("grid nid cannot be 0")

        self.nid=j.application.config.getInt("grid.node.id")

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

