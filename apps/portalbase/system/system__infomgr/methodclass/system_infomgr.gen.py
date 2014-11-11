from JumpScale import j

class system_infomgr(j.code.classGetBase()):
    """
    this is an example actor
    
    """
    def __init__(self):
        
        self._te={}
        self.actorname="infomgr"
        self.appname="system"
        #system_infomgr_osis.__init__(self)
    

        pass

    def addInfo(self, info, **kwargs):
        """
        can be multi line
        param:info dotnotation of info e.g. 'water.white.level.sb 10'  (as used in graphite)
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method addInfo")
    

    def getInfo1h(self, id, start=0, stop=0, **kwargs):
        """
        return raw info (resolution is 1h)
        param:id id in dot noation e.g. 'water.white.level.sb' (can be multiple use comma as separation)
        param:start epoch; 0 means all default=0
        param:stop epoch; 0 means all default=0
        result list(list)
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getInfo1h")
    

    def getInfo1hFromTo(self, id, start, stop, **kwargs):
        """
        will not return more than 12 months of info, resolution = 1h
        param:id id in dot noation e.g. 'water.white.level.sb'
        param:start epoch
        param:stop epoch
        result dict()
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getInfo1hFromTo")
    

    def getInfo5Min(self, id, start=0, stop=0, **kwargs):
        """
        return raw info (resolution is 5min)
        param:id id in dot noation e.g. 'water.white.level.sb' (can be multiple use comma as separation)
        param:start epoch; 0 means all default=0
        param:stop epoch; 0 means all default=0
        result list(list)
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getInfo5Min")
    

    def getInfo5MinFromTo(self, id, start, stop, **kwargs):
        """
        will not return more than 1 month of info
        param:id id in dot noation e.g. 'water.white.level.sb'
        param:start epoch
        param:stop epoch
        result dict()
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getInfo5MinFromTo")
    

    def getInfoWithHeaders(self, id, start, stop, maxvalues=360, **kwargs):
        """
        param:id id in dot noation e.g. 'water.white.level.sb'  (can be multiple use comma as separation)
        param:start epoch
        param:stop epoch
        param:maxvalues nr of values you want to return default=360
        result list(list)
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getInfoWithHeaders")
    

    def reset(self, **kwargs):
        """
        reset all stats
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method reset")
    
