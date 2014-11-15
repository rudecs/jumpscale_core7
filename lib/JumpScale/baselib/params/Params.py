from JumpScale import j
"""
Provides the Params object and the ParamsFactory that is used in the Q-Tree
"""

class ParamsFactory():
    """
    This factory can create new Params objects
    """

    def get(self, dictObject={}):
        """
        Create and return a new Params object
        
        @param dictObject when dict given then dict will be converted into params
        @return: a new Params object
        @rtype: Params
        """
        return Params(dictObject)

    def isParams(self, p):
        """
        Return if the argument object is an instance of Params

        @param p: object to check
        @type p: object
        @return: Whether or not `p` is a Params instance
        @rtype: boolean
        """
        return isinstance(p, Params)

class Params():
    def __init__(self, dictObject=None):
        if dictObject<>None:
            self.__dict__ = dictObject      

    def merge(self, otherParams):
        self.__dict__.update(otherParams.__dict__)

    def get(self, key, defaultvalue=None):
        return self.__dict__.get(key, defaultvalue)

    def __contains__(self, key):
        return key in self.__dict__

    def __getitem__(self, key):
        return self.__dict__[key]

    def expandParamsAsDict(self,**kwargs):
        """
        adds paramsExtra, tags & params from requestContext if it exists
        return as dict

        for each item given as named argument check it is already in dict and if not add
        e.g. args=self.expandParamsAsDict(id=1,name="test")
        will return a dict with id & name and these values unless if they were set in the params already
        can further use it as follows:
        params.result=infomgr.getInfoWithHeaders(**args)

        full example:
        #############
        args=params.expandParamsAsDict(maxvalues=100,id=None,start="-3d",stop=None)

        args["start"]=j.base.time.getEpochAgo(args["start"])
        args["stop"]=j.base.time.getEpochFuture(args["stop"])

        params.result=j.apps.system.infomgr.extensions.infomgr.addInfo(**args)


        """
        params=self
        params2=params.getDict()
        if params.has_key("paramsExtra") and params.paramsExtra<>None:
            params2.update(params.paramsExtra)
        if params.has_key("requestContext") and params.requestContext<>None:
            params2.update(params.requestContext.params)
        if params.has_key("tags") and params2["tags"]<>"":
            params2.update(params2["tags"].getDict())
        for item in ["requestContext","tags","paramsExtra"]:
            if params.has_key(item):
                params2.pop(item)

        if len(kwargs)==0:
            return params2

        result={}
        for key in kwargs.keys():
            if params2.has_key(key):
                result[key]=params2[key]
        return result

    def expandParams(self,**kwargs):
        """
        adds paramsExtra, tags & params from requestContext if it exists
        returns params but not needed because params just get modified to have all these extra arguments/params as properties
        set default as params to this method e.g.
        expandParams(id=10,hight=100)

        """
        def getArgs(d):
            r={}
            reserved=["name","doc","macro","macrostr","cmdstr","page","tags"]
            for key in d.keys():
                if key in reserved:
                    r["arg_%s"%key]=d[key]
                else:
                    r[key]=d[key]
            return r

        if self.has_key("paramsExtra") and self.paramsExtra<>None:
            self.setDict(getArgs(self.paramsExtra))
            # self.pop("paramsExtra")
        if self.has_key("requestContext") and self.requestContext<>None:
            self.setDict(getArgs(self.requestContext.params))
            # self.pop("requestContext")
        if self.has_key("tags") and self.tags<>"":
            self.setDict(getArgs(self.tags.getDict()))
            # self.pop("tags")

        for argname in kwargs.keys():
            if not self.__dict__.has_key(argname):
                self.__dict__[argname]=kwargs[argname]

        return self

    def getTag(self, name, default=None):
        tags = getattr(self, 'tags', None)
        if not tags:
            return default
        tags = tags.getDict()
        tag = tags.get(name)
        if tag and j.tools.text.toStr(tag).startswith('$$'):
            return default
        if not tag:
            return default
        return tag

    def pop(self,key):
        if self.has_key(key):
            self.__dict__.pop(key)

    def has_key(self, key):
        return self.__dict__.has_key(key)

    def getDict(self):
        return self.__dict__

    def setDict(self,dictObject):
        self.__dict__.update(dictObject)

    def extend(self, params):
        """
        Update this Params object with the contents of the argument Params
        object

        @param params: the Params or dict object to update from
        @type params: dict or Params
        @raise TypeError: if the argument is not a dict or Params object
        """
        if isinstance(params, Params):
            d = params.__dict__
        elif isinstance(params, dict):
            d = params
        else:
            raise TypeError("Argument params is of an unknown type %s" %
                    type(params))

        self.__dict__.update(d)

    # def __dir__(self):
    #     return sorted(dir(super(Params, self)) + self.__dict__.keys())

    def __repr__(self):
        parts = ["PARAMS:"]
        for key, value in self.__dict__.iteritems():
            parts.append(" %s:%s" % (key, value))
        return "\n".join(parts)

    def __str__(self):
        return self.__repr__()
