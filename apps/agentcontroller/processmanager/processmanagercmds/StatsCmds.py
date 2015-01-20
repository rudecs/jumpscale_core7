from JumpScale import j


class StatsCmds():
    ORDER=100

    def __init__(self,daemon=None):
        self._name="stats"

        if daemon==None:
            return
        self.daemon=daemon
        self._adminAuth=daemon._adminAuth
        # self.manager= j.tools.startupmanager        

    def listStatKeys(self,prefix="",memonly=False,avgmax=False,session=None):        
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return j.system.stataggregator.list(prefix=prefix,memonly=memonly,avgmax=avgmax)

