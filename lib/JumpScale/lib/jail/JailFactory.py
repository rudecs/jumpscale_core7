from JumpScale import j
import JumpScale.baselib.redis
import ujson as json
import JumpScale.baselib.screen

class JailFactory(object):

    def __init__(self):
        self.redis=j.clients.redis.getByInstance('system')
        self.base="/opt/jsbox"
        if not j.system.fs.exists(path=self.base):
            raise RuntimeError("Please install jsbox (sandbox install for jumpscale)")

    def prepareJSJail(self):
        """
        prepare system we can create jail environments for jumpscale
        """

        j.system.process.execute("chmod -R o-rwx /opt")
        j.system.process.execute("chmod -R o+r /usr")
        j.system.process.execute("chmod -R o-w /usr")
        j.system.process.execute("chmod -R o-w /etc")
        j.system.process.execute("chmod -R o-rwx /home")
        j.system.process.execute("chmod o-rwx /mnt")
        
        # j.system.fs.chmod("/opt/code/jumpscale", 0o777)
        j.system.fs.chown("/opt", "root")
        j.system.process.execute("chmod 777 /opt")

        #SHOULD WE ALSO DO NEXT?
        # j.system.fs.chmod("/opt/code", 0o700)
        j.system.process.execute("chmod 700 /opt/code")
        
        # j.system.process.execute("chmod 777 /opt/jumpscale")
        # j.system.process.execute("chmod -R 777 /opt/jumpscale7/bin")
        # j.system.process.execute("chmod -R 777 /opt/jumpscale7/lib")
        # j.system.process.execute("chmod -R 777 /opt/jumpscale7/libext")
        # j.system.process.execute("chmod 777 /opt/code")

        j.system.process.execute("chmod 777 %s"%self.base)
        j.system.process.execute("chmod 777 /home")

        logdir="/tmp/tmuxsessions"
        j.system.fs.createDir(logdir)
        j.system.process.execute("chmod 777 %s"%logdir)


    def _createJSJailEnv(self,user,secret):
        """
        create jumpscale jail environment for 1 user
        """
        self.killSessions(user)

        j.system.unix.addSystemUser(user,None,"/bin/bash","/home/%s"%user)
        j.system.unix.setUnixUserPassword(user,secret)
        j.system.fs.copyDirTree("%s/apps/jail/defaultenv"%self.base,"/home/%s"%(user))
        j.system.fs.symlink("%s/bin"%self.base,"/home/%s/jumpscale/bin"%(user))
        j.system.fs.symlink("%s/lib"%self.base,"/home/%s/jumpscale/lib"%(user))
        j.system.fs.symlink("%s/libext"%self.base,"/home/%s/jumpscale/libext"%(user))
        j.system.fs.createDir("/home/%s/jumpscale/apps"%user)
        # j.system.fs.symlink("/opt/code/jumpscale/default__jumpscale_examples/examples/","/home/%s/jumpscale/apps/examples"%user)
        # j.system.fs.symlink("/opt/code/jumpscale/default__jumpscale_examples/prototypes/","/home/%s/jumpscale/apps/prototypes"%user)
        
        # def portals():
        #     j.system.fs.symlink("/opt/code/jumpscale/default__jumpscale_portal/apps/portalbase/","/home/%s/jumpscale/apps/portalbase"%user)
        #     j.system.fs.symlink("/opt/code/jumpscale/default__jumpscale_portal/apps/portalexample/","/home/%s/jumpscale/apps/portalexample"%user)
        #     src="/opt/code/jumpscale/default__jumpscale_grid/apps/incubaidportals/"
        #     j.system.fs.copyDirTree(src,"/home/%s/jumpscale/apps/incubaidportals"%user)
        # portals()

        # src="/opt/code/jumpscale/default__jumpscale_lib/apps/cloudrobot/"
        # j.system.fs.copyDirTree(src,"/home/%s/jumpscale/apps/cloudrobot"%user)

        # src="/opt/code/jumpscale/default__jumpscale_core/apps/admin/"
        # j.system.fs.copyDirTree(src,"/home/%s/jumpscale/apps/admin"%user)

        j.system.process.execute("chmod -R ug+rw /home/%s"%user)
        j.system.fs.chown("/home/%s"%user, user)
        j.system.process.execute("rm -rf /tmp/mc-%s"%user)

        secrpath="/home/%s/.secret"%user
        j.system.fs.writeFile(filename=secrpath,contents=secret)

        j.system.fs.writeFile("/etc/sudoers.d/%s"%user,"%s ALL = (root) NOPASSWD:ALL"%user)
        

    def listSessions(self,user):
        return j.system.platform.screen.getSessions(user="user1")
        # res=[]
        # try:
        #     rc,out=j.system.process.execute("sudo -i -u %s tmux list-sessions"%user)
        # except Exception,e:
        #     if str(e).find("Connection refused") != -1:
        #         return []
        #     print "Exception in listsessions:%s"%e
        #     return []
        # for line in out.split("\n"):
        #     if line.strip()=="":
        #         continue
        #     if line.find(":") != -1:
        #         name=line.split(":",1)[0].strip()
        #         res.append(name)
        # return res

    def killSessions(self,user):
        j.system.process.killUserProcesses(user)
        j.system.fs.removeDirTree("/home/%s"%user)        
        j.system.unix.removeUnixUser(user, removehome=True,die=False)
        user=user.strip()
        keys=self.redis.hkeys("robot:sessions")
        for key in keys:
            user2,session=key.split("__")
            if user==user2.strip():
                data=self.redis.hget("robot:sessions",key)
                session=json.loads(data)
                for pid in session["pids"]:
                    if j.system.process.isPidAlive(pid):
                        j.system.process.kill(pid)
                        # print "KILL %s"%pid
                self.redis.hdel("robot:sessions",key)
        
            
    def killAllSessions(self):
        for user in  j.system.fs.listDirsInDir("/home",False,True):
            secrpath="/home/%s/.secret"%user
            if j.system.fs.exists(path=secrpath):
                self.killSessions(user)
        cmd="killall shellinaboxd"
        j.system.process.execute(cmd)

    def send2session(self,user,session,cmd):
        j.system.process.execute("sudo -u %s -i tmux send -t %s %s ENTER"%(user,session,cmd))

    def createJSJailSession(self,user,secret,session,cmd=None):
        self._createJSJailEnv(user,secret)
        # secrpath="/home/%s/.secret"%user
        # secret=j.system.fs.fileGetContents(secrpath).strip()

        #check session exists
        sessions=self.listSessions(user)
        if not session in sessions:
            #need to create session
            cmd="sudo -u %s -i tmux new-session -d -s %s"%(user,session)
            
            j.system.process.execute(cmd)
            j.system.process.execute("sudo -u %s -i tmux set-option -t %s status off"%(user,session))
            if cmd!=None:
                self.send2session(user,session,"clear")  


            

             
