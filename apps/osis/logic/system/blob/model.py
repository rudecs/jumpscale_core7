from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Blob(OsisBaseObject):

    """
    identifies a job in the grid
    """

    def __init__(self, ddict={}, value=None):
        import time
        if ddict != {}:
            self.load(ddict)
        else:
            self.value = value

    def getUniqueKey(self):
        return j.base.idgenerator.generateGUID()

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        if not self.guid:
            self.guid = self.getUniqueKey()
        return self.guid
