from JumpScale import j
join = j.system.fs.joinPaths

class AgentPyApps:
    agentguid = "agent1"
    agentcontrollerguid = "agentcontroller"

    def __init__(self, appName):
        self.appName = appName
    
    def generate_cfg(self):
        configfile = j.config.getInifile('agent')
        if not configfile.checkSection(self.appName):
            configfile.addSection(self.appName)
        configfile.addParam(self.appName, "domain", self.appName)
        configfile.addParam(self.appName, 
                        "agentcontrollerguid", self.agentcontrollerguid)
        configfile.addParam(self.appName, "hostname", self.appName)
        configfile.addParam(self.appName, "xmppserver", "127.0.0.1")
        configfile.addParam(self.appName, "agentguid", self.agentguid)
        configfile.addParam(self.appName, "password", self.appName)
        configfile.write()

    @property
    def password(self):
        return self.appName

    @property
    def hostname(self):
        return self.appName
