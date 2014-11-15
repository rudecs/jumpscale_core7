from JumpScale import j
join = j.system.fs.joinPaths

class ArakoonPyApps:

    def __init__(self, appName):
        self.appName = appName
    
    def generate_cfg(self, baseport):
        config = j.clients.arakoon.getClientConfig(self.appName)
        if config.getNodes():
            return
        baseport = int(baseport)
        s = j.manage.arakoon.getCluster(self.appName)
        if not s.listNodes():
            s.setUp(1, baseport)
        config = j.clients.arakoon.getClientConfig(self.appName)
        if not config.getNodes():
            config.generateFromServerConfig()
