from .network import UnixNetworkManager
from JumpScale import j
import os

class UnixManagerFactory(object):
    def get(self, connection=None):
        """
        Returns Unix Manager
        """
        return UnixManager(connection)

class UnixManager(object):
    """
    Unix Manager
    """
    def __init__(self, connection=None):
        if connection==None:
            connection=j.ssh.connection

        self._con = connection
        

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
        self._net = UnixNetworkManager(self)
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

    def changePasswd(self,passwd,login="root"):
        print passwd
        self.connection.run('echo "{username}:{password}" | chpasswd'.format(
            username=login,
            password=passwd)
        )

    def getUsers(self):
        users=self.find("/home",recursive=False)
        users=[j.do.getBaseName(item) for item in users if (item.strip()!="" and item.strip("/")!="home")]
        return users        

    def secureSSH(self,sshkey="",recoverypasswd=""):
        """
        #will set recovery passwd for root
        will disable all other users to use ssh
        will authorize secure ssh key (is the rsa pub key as text)
        """
        print "change passwd"
        if recoverypasswd=="" and os.environ.has_key("recoverypasswd"): 
            recoverypasswd=os.environ["recoverypasswd"]
        self.changePasswd(recoverypasswd)
        if len(recoverypasswd)<8:
            j.events.opserror_critical("Choose longer passwd")
        print "ok"

        def check():
            self.connection.fabric.api.env.password = recoverypasswd
            old=self.connection.fabric.key_filename
            print "test ssh connection over recovery"
            if not self.connection.dir_exists("/etc")==True:
                j.events.opserror_critical("could not login with recovery passwd, cannot secure ssh session.")
            self.connection.fabric.key_filename=old
            print "ok"
        
        check()

        self.connection.dir_remove("/root/.ssh")
        self.connection.dir_ensure("/root/.ssh")
        check()

        if sshkey=="":
            #try to load from connection
            from IPython import embed
            print "DEBUG NOW ououoiuoi"
            embed()
            
        self.connection.ssh_authorize("root",sshkey)

        self.connection.fabric.api.env.password=""
        print "test ssh with secure key"
        if not self.connection.dir_exists("/etc")==True:
            j.events.opserror_critical("could not login with secure key from current system, has right sshpub key been used in relation to local private key?")
        print "ok"


        from IPython import embed
        print "DEBUG NOW secureSSH"
        embed()
        
        
    def executeBashScript(self,content):
        if content[-1]!="\n":
            content+="\n"
        content+="\necho **DONE**\n"
        path="/tmp/%s.sh"%j.base.idgenerator.generateRandomInt(0,10000)
        self.connection.file_write(location=path, content=content, mode=0770, owner="root", group="root", sudo=True)
        out=self.connection.run("sh %s"%path, shell=True, pty=True, combine_stderr=True)
        self.connection.file_unlink(path)
        lastline=out.split("\n")[-1]
        if lastline.find("**DONE**")==-1:
            from IPython import embed
            print "DEBUG NOW 9999"
            embed()            
            raise RuntimeError("Could not execute bash script.\n%s\nout:%s\n"%(content,out))
        return "\n".join(out.split("\n")[:-1])

    def find(self,path,recursive=True,pattern="",findstatement="",type="",contentsearch="",extendinfo=False):
        """
        @param findstatement can be used if you want to use your own find arguments
        for help on find see http://www.gnu.org/software/findutils/manual/html_mono/find.html

        @param pattern e.g. */config/j* 

            *   Matches any zero or more characters.
            ?   Matches any one character.
            [string] Matches exactly one character that is a member of the string string. 

        @param type

            b    block (buffered) special
            c    character (unbuffered) special
            d    directory
            p    named pipe (FIFO)
            f    regular file
            l    symbolic link

        @param contentsearch
            looks for this content inside the files

        @param extendinfo   : this will return [[$path,$sizeinkb,$epochmod]]

        """
        cmd="find %s"%path
        if recursive==False:
            cmd+=" -maxdepth 1"
        if contentsearch=="" and extendinfo==False: 
            cmd+=" -print"
        if pattern!="":
            cmd+=" -path '%s'"%pattern
        if contentsearch!="":
            type="f"

        if type!="":
            cmd+=" -type %s"%type

        if extendinfo:
            cmd+=" -printf '%p||%k||%T@\n'"

        if contentsearch!="":
            cmd+=" -print0 | xargs -r -0 grep -l '%s'"%contentsearch

        out=self.connection.run(cmd)

        paths=[item.strip() for item in out.split("\n")]

        # print cmd

        paths2=[]
        if extendinfo:
            for item in paths:
                path,size,mod=item.split("||")
                if path.strip()=="":
                    continue
                paths2.append([path,int(size),int(float(mod))])
        else:
            paths2=[item for item in paths if item.strip()!=""]

        return paths2

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


