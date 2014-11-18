from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class Test(OsisBaseObject):

    """
    identifies a test in the grid
    """

    def __init__(self, ddict={}, gid=0, jsname='', jsorganization='', roles=[], args=[], timeout=60, sessionid=None, jscriptid=None,lock="",\
            lockduration=3600,nid=0):
        if ddict != {}:
            self.load(ddict)
        else:
            self.id=0
            self.name=""
            self.testrun="" 
            self.path=""
            self.state="" #OK, ERROR, DISABLED
            self.priority=0 #lower is highest priority
            self.organization=""
            self.author=""
            self.version=0
            self.categories=[]
            self.starttime = 0
            self.endtime = 0
            self.enable=True
            self.result={}
            self.output={}
            self.eco={}
            self.license = ""
            self.source={}
            self.gid =gid
            self.nid =nid

    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        return self.getSetGuid()

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.id = int(self.id)
        self.guid = "%s_%s" % (self.gid, self.id)
        return self.guid

