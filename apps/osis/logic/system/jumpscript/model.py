from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()


class Jumpscript(OsisBaseObject):

    """
    identifies a Jumpscript in the grid
    """

    def __init__(self, ddict={},name="", category="", organization="", author="", license="", version="", roles="", action=None, source="", path="", descr=""):
        
        if ddict != {}:
            self.load(ddict)
            if self.id is None:
                self.id = 0
        else:
            self.id=0
            self.gid =j.application.whoAmI.gid
            self.name = name
            self.descr = descr
            self.category = category
            self.organization = organization
            self.author = author
            self.license = license
            self.version = version
            self.roles = roles
            if action!=None:
                self.setArgs(action)
            else:
                self.args=[]
                # self.argsDefaults = args.defaults
                # self.argsVarArgs = args.varargs
                # self.argsKeywords = args.keywords

            self.source = source
            self.path = path
            self.enabled=True
            self.async=True
            self.period=0
            self.order=0
            self.queue=""
            self.log=True

    def setArgs(self,action):
        import inspect
        args = inspect.getargspec(action)
            # args.args.remove("session")
            # methods[name] = {'args' : args, 'doc': inspect.getdoc(method)}
        self.args = args.args
        self.argsDefaults = args.defaults
        self.argsVarArgs = args.varargs
        self.argsKeywords = args.keywords


    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        return j.base.byteprocessor.hashTiger160(str([self.organization,self.category,self.version,self.name,self.gid,self.source, self.roles, self.queue]))  # need to make sure roles & source cannot be changed

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        self.id = int(self.id)
        self.guid = "%s_%s"%(self.gid,self.id)
        return self.guid

    def getContentKey(self):
        """
        is like returning the hash, is used to see if object changed
        """
        out=""
        for item in ["gid","args","roles","source"]:
            out+=str(self.__dict__.get(item))
        return j.tools.hash.md5_string(out)
            

       
