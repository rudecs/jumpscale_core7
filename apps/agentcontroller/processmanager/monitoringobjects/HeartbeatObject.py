from JumpScale import j

from _MonObjectBaseFactory import MonObjectBaseFactory, MonObjectBase

class HeartbeatObjectFactory(MonObjectBaseFactory):
    def __init__(self,host,classs):
        MonObjectBaseFactory.__init__(self,host,classs)
        self.osis=j.clients.osis.getCategory(self.host.daemon.osis,"system","heartbeat")


class HeartbeatObject(MonObjectBase):
    pass
