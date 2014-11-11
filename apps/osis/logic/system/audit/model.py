from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Audit(OsisBaseObject):

    """
    identifies a job in the grid
    """

    def __init__(self, ddict={}, user="", call=None, args=None, kwargs=None, statuscode=None, result=None):
        import time
        if ddict <> {}:
            self.load(ddict)
        else:
            self.guid = None
            self.user = user
            self.result = result
            self.call = call
            self.statuscode = statuscode
            self.args = args
            self.kwargs = kwargs
            self.timestamp = time.time()

    def getUniqueKey(self):
        return j.base.idgenerator.generateGUID()

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        if not self.guid:
            self.guid = self.getUniqueKey()
        return self.guid
