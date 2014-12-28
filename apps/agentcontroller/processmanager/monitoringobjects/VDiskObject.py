from JumpScale import j

from _MonObjectBaseFactory import MonObjectBaseFactory, MonObjectBase

class VDiskObjectFactory(MonObjectBaseFactory):
    def __init__(self,host,classs):
        MonObjectBaseFactory.__init__(self,host,classs)
        self.osis=j.core.osis.getClientForCategory(self.host.daemon.osis,"system","vdisk")
        #@todo P1 load them from ES at start (otherwise delete will not work), make sure they are proper osis objects


class VDiskObject(MonObjectBase):
    pass
