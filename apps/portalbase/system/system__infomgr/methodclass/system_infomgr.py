from JumpScale import j


class system_infomgr(j.code.classGetBase()):

    """
    this is an example actor
    
    """

    def __init__(self):

        self._te = {}
        self.actorname = "infomgr"
        self.appname = "system"

    def addInfo(self, info, **args):
        """
        can be multi line
        param:info dotnotation of info e.g. 'water.white.level.sb 10'  (as used in graphite)
        result bool 
        
        """
        return j.apps.system.infomgr.extensions.infomgr.addInfo(info)

    def getInfo1h(self, id, start, stop, **args):
        """
        return raw info (resolution is 1h)
        param:id id in dot noation e.g. 'water.white.level.sb' (can be multiple use comma as separation)
        param:start epoch; 0 means all
        param:stop epoch; 0 means all
        result list(list) 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method getInfo1h")

    def getInfo1hFromTo(self, id, start, stop, **args):
        """
        will not return more than 12 months of info, resolution = 1h
        param:id id in dot noation e.g. 'water.white.level.sb'
        param:start epoch
        param:stop epoch
        result dict() 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method getInfo1hFromTo")

    def getInfo5Min(self, id, start, stop, **args):
        """
        return raw info (resolution is 5min)
        param:id id in dot noation e.g. 'water.white.level.sb' (can be multiple use comma as separation)
        param:start epoch; 0 means all
        param:stop epoch; 0 means all
        result list(list) 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method getInfo5Min")

    def getInfo5MinFromTo(self, id, start, stop, **args):
        """
        will not return more than 1 month of info
        param:id id in dot noation e.g. 'water.white.level.sb'
        param:start epoch
        param:stop epoch
        result dict() 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method getInfo5MinFromTo")

    def getInfoWithHeaders(self, id, start, stop, maxvalues, **args):
        """
        param:id id in dot noation e.g. 'water.white.level.sb'  (can be multiple use comma as separation)
        param:start epoch
        param:stop epoch
        param:maxvalues nr of values you want to return
        result list(list) 
        
        """
        result = j.apps.system.infomgr.extensions.infomgr.getInfoWithHeaders(maxvalues=100, id=id, start=start, stop=stop)

        return result

    def reset(self, **args):
        """
        reset all stats
        result bool 
        
        """
        j.apps.system.infomgr.extensions.infomgr.reset()
        return "RESET DONE"
