from .network import UnixNetworkManager
from JumpScale import j
import os

import paramiko

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
        script=j.tools.text.lstrip(script)
        path="/tmp/jumpscript_temp_%s.py"%j.base.idgenerator.generateRandomInt(1,10000)
        self.connection.file_write(path,script)
        out=self.executeRemoteTmuxCmd("jspython %s"%path)
        self.connection.file_unlink(path)
        return out

    def changePasswd(self,passwd,login="recovery"):
        if len(passwd)<6:
            j.events.opserror_critical("Choose longer passwd in changePasswd")        
        self.connection.run('echo "{username}:{password}" | chpasswd'.format(
            username=login,
            password=passwd)
        )

    def getUsers(self):
        users=self.find("/home",recursive=False)
        users=[j.do.getBaseName(item) for item in users if (item.strip()!="" and item.strip("/")!="home")]
        return users        

    def secureSSH(self,sshkeypath="",recoverypasswd=""):
        """
        * actions
            * will set recovery passwd for user recovery
            * will create a recovery user account
            * will disable all other users to use ssh (so only user 'recovery' can login & do sudo -s)
            * will authorize key identified with sshkeypath
            * will do some tricks to secure sshdaemon e.g. no pam, no root access.
        * locked down server where only the specified key can access and through the recovery created user

        @param sshkeypath if =="" then will not set the ssh keys only work with recovery passwd

        """

        if sshkeypath!="" and not j.system.fs.exists(sshkeypath):
            j.events.opserror_critical("Cannot find key on %s"%sshkeypath)

        if recoverypasswd=="" and os.environ.has_key("recoverypasswd"): 
            recoverypasswd=os.environ["recoverypasswd"]
        
        if len(recoverypasswd)<6:
            j.events.opserror_critical("Choose longer passwd (min 6), do this by doing 'export recoverypasswd=something' before running this script.")            

        if sshkeypath!="":
            sshkeypub=j.system.fs.fileGetContents(sshkeypath+".pub")

        def checkkeyavailable(sshkeypub):
            errormsg="Could not find SSH agent, please start by 'eval \"$(ssh-agent -s)\"' before running this cmd,\nand make sure appropriate keys are added with ssh-add ..."
            sshkeypubcontent=" ".join(sshkeypub.split(" ")[1:]).strip().split("==")[0]+"=="
            #check if current priv key is in ssh-agent
            agent=paramiko.agent.Agent()
            try:
                keys=agent.get_keys()
            except Exception,e:
                j.events.opserror_critical( errormsg)
            
            if keys==():
                j.events.opserror_critical( errormsg)                

            for key in keys:
                if key.get_base64()==sshkeypubcontent:
                    return True
            return False

        if sshkeypath!="" and not checkkeyavailable(sshkeypub):
            #add the new key
            j.do.executeInteractive("ssh-add %s"%sshkeypath)

        #make sure recovery user exists
        if self.connection.dir_exists("/home/recovery"):
            self.connection.dir_remove("/home/recovery/")
            self.connection.user_remove("recovery")        
        
        self.connection.user_ensure("recovery",recoverypasswd)

        print "change passwd"
        self.changePasswd(recoverypasswd)
        print "ok"
                    
        print "test ssh connection only using the recovery user: login/passwd combination"
        ssh = paramiko.SSHClient()
        hostname=self.connection.host().split(":")[0]
        port=int(self.connection.host().split(":")[1])
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port=port, username="recovery", password=recoverypasswd, pkey=None, key_filename=None, timeout=None, allow_agent=False, look_for_keys=False)
        ssh.close()
        print "ssh recovery user ok"
        
        if sshkeypath!="":
            self.connection.dir_remove("/root/.ssh")
            self.connection.dir_ensure("/root/.ssh")
                
            self.connection.ssh_authorize("root",sshkeypub)

            print "test ssh connection with pkey"
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        CMDS="""
        #make sure user is in sudo group
        usermod -a -G sudo recovery

        #sed -i -e '/texttofind/ s/texttoreplace/newvalue/' /path/to/file
        sed -i -e '/.*PermitRootLogin.*/ s/.*/PermitRootLogin without-password/' /etc/ssh/sshd_config
        sed -i -e '/.*UsePAM.*/ s/.*/UsePAM no/' /etc/ssh/sshd_config
        sed -i -e '/.*Protocol.*/ s/.*/Protocol 2/' /etc/ssh/sshd_config

        #only allow root & recovery user (make sure it exists)
        sed -i -e '/.*AllowUsers.*/d' /etc/ssh/sshd_config
        echo '' >> /etc/ssh/sshd_config
        echo 'AllowUsers root' >> /etc/ssh/sshd_config
        echo 'AllowUsers recovery' >> /etc/ssh/sshd_config

        /etc/init.d/ssh restart
        """
        self.executeBashScript(CMDS)

        if sshkeypath!="":
            #play with paramiko to see if we can connect (ssh-agent will be used)
            ssh.connect(hostname, port=port, username="root", password=None, pkey=None, key_filename=None, timeout=None, allow_agent=True, look_for_keys=False)
            ssh.close()
            print "ssh test with key ok"

        print "secure machine done"
    
    def executeBashScript(self,content):
        content=j.tools.text.lstrip(content)
        if content[-1]!="\n":
            content+="\n"
        content+="\necho **DONE**\n"
        path="/tmp/%s.sh"%j.base.idgenerator.generateRandomInt(0,10000)
        self.connection.file_write(location=path, content=content, mode=0770, owner="root", group="root", sudo=True)
        out=self.connection.run("sh %s"%path, shell=True, pty=True, combine_stderr=True)
        self.connection.file_unlink(path)
        lastline=out.split("\n")[-1]
        if lastline.find("**DONE**")==-1:           
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
        @param script is the content of the script
        """
        path="/tmp/jumpscript_temp_%s.py"%j.base.idgenerator.generateRandomInt(1,10000)
        self.connection.file_write(path,script)
        out=self.executeRemoteTmuxCmd("jspython %s"%path)
        self.connection.file_unlink(path)
        return out


