from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Health(OsisBaseObject):

    """
    identifies a health in the grid
    """

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.guid = '%s_%s_%s' % (self.gid, self.nid, self.cmd)
        return self.guid


