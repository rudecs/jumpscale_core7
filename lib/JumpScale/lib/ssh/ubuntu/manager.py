from .network import NetworkManager
from JumpScale import j

class UbuntuManagerFactory(object):
    def get(self, connection=None):
        """
        Returns Ubuntu Manager
        """
        return UbuntuManager(connection)

class UbuntuManager(object):
    """
    Ubuntu Manager
    """
    def __init__(self, connection=None):
        if connection==None:
            connection=j.ssh.connection

        self._con = connection
        self._net = NetworkManager(self)
        
    @property
    def connection(self):
        """
        Connection manager
        """
        return self._con
    
    @property
    def network(self):
        """
        Network manager
        """
        return self._net

    def executeRemoteTmuxCmd(self,cmd):
        res=self.connection.run("tmux has-session -t cmd 2>&1 ;echo")
        if not res.find("session not found")==-1:
            self.connection.run("tmux new-session -s cmd -d")
        self.connection.file_unlink("/tmp/tmuxout")
        self.connection.run("tmux send -t cmd '%s > /tmp/tmuxout 2>&1;echo **DONE**>> /tmp/tmuxout 2>&1' ENTER"%cmd)
        out=self.connection.file_read("/tmp/tmuxout")
        self.connection.file_unlink("/tmp/tmuxout")
        if out.find("**DONE**")==-1:
            j.events.opserror_critical("Cannot execute %s on tmux on remote %s.\nError:\n%s"%(cmd,self.connection.fabric.state.connections.keys(),out))
        out=out.replace("**DONE**","")
        return out


    def executeRemoteTmuxJumpscript(self,script):
        """
        execute a jumpscript (script as content) in a remote tmux command, the stdout will be returned
        """
        path="/tmp/jumpscript_temp_%s.py"%j.base.idgenerator.generateRandomInt(1,10000)
        self.connection.file_write(path,script)
        out=self.executeRemoteTmuxCmd("jspython %s"%path)
        self.connection.file_unlink(path)
        return out        