from JumpScale import j


class StartupManagerCmds():
    ORDER=100

    def __init__(self,daemon=None):
        self._name="startupmanager"

        if daemon==None:
            return

        self.daemon=daemon
        self._adminAuth=daemon._adminAuth
        self.manager= j.tools.startupmanager        

    def _getJPackage(self, domain, name):
        jps = j.packages.find(domain, name, installed=True)
        if not jps:
            raise RuntimeError('Could not find installed jpackage with domain %s and name %s' % (domain, name))
        return jps[0]


    def getDomains(self,session=None,**args):
        return self.manager.getDomains()

    def startAll(self,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return self.manager.startAll()

    def removeProcess(self,domain, name,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return self.manager.removeProcess(domain, name)

    def getStatus4JPackage(self,domain, name,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd) 
        jpackage=self._getJPackage(domain,name)       
        return self.manager.getStatus4JPackage(jpackage)

    def getStatus(self, domain, name,session=None,**args):
        """
        get status of process, True if status ok
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return self.manager.getStatus( domain, name)

    def listProcesses(self,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return [item.split("__") for item in self.manager.listProcesses()]

    def getProcessesActive(self, domain=None, name=None, session=None,**kwargs):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        result = list()
        for pd in self.manager.getProcessDefs(domain, name):
            item = dict()
            item['status'] = pd.isRunning()
            if item['status']:
                item['pid'] = pd.pid
            else:
                item['pid'] = 0
                
            item['name'] = pd.name
            item['domain'] = pd.domain
            item['autostart'] = pd.autostart == '1'
            item['cmd'] = pd.cmd
            item['args'] = pd.args
            item['args'] = pd.args
            item['ports'] = pd.ports
            item['priority'] = pd.priority
            item['workingdir'] = pd.workingdir
            item['env'] = pd.env
            result.append(item)
        return result


    def startProcess(self, domain="", name="", timeout=20,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return self.manager.startProcess( domain, name, timeout)

    def stopProcess(self, domain,name, timeout=20,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return self.manager.stopProcess(domain,name, timeout)

    def disableProcess(self, domain,name, timeout=20,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return self.manager.disableProcess( domain,name, timeout)

    def enableProcess(self, domain,name, timeout=20,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return self.manager.enableProcess( domain,name, timeout)

    def restartProcess(self, domain,name,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)
        return self.manager.restartProcess( domain,name)

    def reloadProcess(self, domain, name,session=None,**args):
        if session<>None:
            self._adminAuth(session.user,session.passwd)
        return self.manager.reloadProcess( domain,name)



