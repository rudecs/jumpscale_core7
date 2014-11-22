from JumpScale import j
import os
import JumpScale.baselib.screen
import time
import signal
try:
    import ujson as json
except ImportError:
    import json

class ProcessNotFoundException(Exception):
    pass

class ProcessDefEmpty:
    def __init__(self,name):
        self.autostart=False
        self.path=""
        self.pids=[]
        self.parentpid=0
        self.procname=name
        if name.find(":")!=-1:
            domain,name=name.split(":")
        else:
            domain=""
        self.name=name
        self.domain=domain
        self.user=""
        self.cmd=""
        self.args=""
        self.env=""
        self.priority=0
        self.check=False
        self.isJSapp=True
        self.timeout=1
        self.reload_signal=0
        self.stopcmd = ""
        self.plog=False
        self.numprocesses = 0
        self.workingdir=""
        self.ports=[]
        self.jpackage_domain=""
        self.jpackage_name=""
        self.jpackage_version=""
        self.jpackage_instance=""
        self.lastCheck=int(time.time())
        self.upstart = False
        self.inprocessmanager=False #mans will be dealt with by our own processmanager
        self.processfilterstr=""
        self.system=True
        self.isRunning()

    def isRunning(self):
        self.pids=j.system.process.appGetPidsActive(self.name)
        self.numprocesses=len(self.pids)
        return len(self.pids)>0

    def getPids(self):
        return j.system.process.appGetPidsActive(self.name)

    def __str__(self):
        if self.system:
            s="S"
        else:
            s=" "
        if self.isJSapp:
            j="J"
        else:
            j=" "
        out="%-20s %-20s %-2s %-2s %s"%(self.domain,self.name,s,j,self.processfilterstr)
        return out

    __repr__=__str__

class ProcessDef:
    def __init__(self, hrd,path):
        self.hrd=hrd
        self.system=False
        self.autostart=hrd.getInt("process.autostart")==1
        
        self.path=path
        self.name=hrd.get("process.name")
        self.domain=hrd.get("process.domain")
        self.user=hrd.get("process.user",default=False)
        if self.user==False:
            self.user="root"
        self.cmd=self._replaceSysVars(hrd.getStr("process.cmd"))
        self.args=self._replaceSysVars(hrd.getStr("process.args"))

        self.env=hrd.getDict("process.env")
        self.procname="%s:%s"%(self.domain,self.name)
        self.env["JSPROCNAME"]=self.procname #set env variable so app can start using right name

        if j.application.sandbox:
            if "LD_LIBRARY_PATH" not in self.env:
                self.env["LD_LIBRARY_PATH"]="%s/bin"%j.dirs.baseDir
            if "JSBASE" not in self.env:
                self.env["JSBASE"]="%s"%j.dirs.baseDir
            if "PYTHONPATH" not in self.env:
                self.env["PYTHONPATH"]="%s/lib:%s/python.zip:%s/libjs"%(j.dirs.baseDir,j.dirs.baseDir,j.dirs.baseDir)
            if "PATH" not in self.env:
                self.env["PATH"]="%s/tools:%s/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"%(j.dirs.baseDir,j.dirs.baseDir)


        self.priority=hrd.getInt("process.priority")

        self.check=hrd.getBool("process.check",default=True)

        self.isJSapp=hrd.getBool("process.isJSapp",default=True)

        self.timeout=hrd.getInt("process.timeoutcheck",default=10)

        if self.timeout<2:
            self.timeout=2
            hrd.set("process.timeoutcheck",2)

        self.reload_signal=0
        if hrd.exists('process.reloadsignal'):
            self.reload_signal = hrd.getInt("process.reloadsignal")
        else:
            self.reload_signal = None

        self.stopcmd = self._replaceSysVars(hrd.get("process.stopcmd",default=""))

        self.plog=hrd.getBool("process.log",default=True)

        self.numprocesses = hrd.getInt('process.numprocesses',default=1)

        self.workingdir=self._replaceSysVars(hrd.get("process.workingdir"))
        ports=hrd.getList("process.ports")
        ports = [port for port in ports if str(port).strip()!=""]
        self.ports=list(set(ports))

        self.jpackage_domain=hrd.get("process.jpackage.domain")
        self.jpackage_name=hrd.get("process.jpackage.name")
        self.jpackage_version=hrd.get("process.jpackage.version")
        if hrd.exists("process.jpackage.instance"):
            self.jpackage_instance=hrd.get("process.jpackage.instance")
        else:
            self.jpackage_instance="0"

        self.upstart = self.hrd.getBool("process.upstart",default=False)

        if self.upstart:
            self.logfile="/var/log/upstart/%s.log"%self.name
        else:
            self.logfile = j.system.fs.joinPaths(StartupManager.LOGDIR, "%s_%s_%s.log" % (self.domain, self.name,j.base.time.get5MinuteId()))

        if not j.system.fs.exists(self.logfile):
            j.system.fs.createDir(StartupManager.LOGDIR)
            j.system.fs.createEmptyFile(self.logfile)
        else:
            j.system.fs.remove(self.logfile)

        self._nameLong=self.name
        while len(self._nameLong)<20:
            self._nameLong+=" "
        self.lastCheck=0
        self.lastMeasurements={}

        if self.hrd.exists("process.active"):
            self.hrd.delete("process.active")

        if self.hrd.exists("process_active"):
            self.hrd.delete("process_active")

        if self.hrd.exists("process.pid"):
            self.hrd.delete("process.pid")

        if self.hrd.exists("pid"):
            self.hrd.delete("pid")

        self.processfilterstr=self.hrd.get("process.processfilterstr",default="")

        if self.isJSapp==False and self.processfilterstr=="":
            self.raiseError("Need to specify process.filterstring if isJSapp==False")

        self.pids=[]

    def raiseError(self,msg):
        msg="Error for process %s:%s\n%s"%(self.domain,self.name,msg)
        j.errorconditionhandler.raiseOperationalCritical(msg,category="jsprocess")

    def _replaceSysVars(self,txt):
        txt=txt.replace("$base",j.dirs.baseDir)
        return txt

    def getJSPid(self):
        return "g%s.n%s.%s"%(j.application.whoAmI.gid,j.application.whoAmI.nid,self.name)

    def log(self,msg):
        print("%s: %s"%(self._nameLong,msg))

    def registerToRedis(self):
        if j.application.redis==None and self.name=="redis_system":
            #this is to bootstrap
            self.start()
            j.application.connectRedis()
            return
        
        if j.application.redis==None:
            j.events.opserror_critical("Cannot find running redis on port 9999, cannot register %s"%self)

        if j.application.redis.hexists("application",self.procname):
            pids=json.loads(j.application.redis.hget("application",self.procname))
        else:
            pids=[]
        
        for pid in self.pids:
            if pid not in pids:
                pids.append(pid)
        j.application.redis.hset("application",self.procname,json.dumps(pids))        

    def start(self):
        # self.logToStartupLog("***START***")

        if self.autostart==False:
            self.log("no need to start, disabled.")
            return

        if self.isRunning(wait=False):
            self.log("no need to start, already started.")
            return

        if self.jpackage_domain!="":
            try:
                jp=j.packages.find(self.jpackage_domain,self.jpackage_name)[0]
            except Exception as e:
                self.raiseError("COULD NOT FIND JPACKAGE")

        self.log("process dependency CHECK")
        jp.processDepCheck()
        self.log("process dependency OK")
        self.log("start process")

        cmd=self._replaceSysVars(self.cmd)
        args=self._replaceSysVars(self.args)

        #make sure we cleanup past if any
        if self.upstart and j.tools.startupmanager.upstart==False:
            spath="/etc/init/%s.conf"%self.name
            if j.system.fs.exists(path=spath):
                j.system.platform.ubuntu.stopService(self.name)
                if j.tools.startupmanager.upstart==False:
                    j.system.fs.remove(spath)  
            cmd2="%s %s"%(cmd,args)  #@todo no support for working dir yet
            j.system.fs.writeFile(self.logfile,"start cmd:\n%s\n"%cmd2,True)#append
            j.system.process.executeIndependant(cmd2)            

        elif not self.upstart or j.tools.startupmanager.upstart==False:

            for i in range(1, self.numprocesses+1):
                name="%s_%s"%(self.name,i)
                for tmuxkey,tmuxname in j.system.platform.screen.getWindows(self.domain).items():
                    if tmuxname==name:
                        j.system.platform.screen.killWindow(self.domain,name)
                tcmd = cmd.replace("$numprocess", str(i))
                targs = args.replace("$numprocess", str(i))

                j.system.platform.screen.executeInScreen(self.domain,name,tcmd+" "+targs,cwd=self.workingdir, env=self.env,user=self.user)#, newscr=True)

                if self.plog:
                    logfile="%s.%s"%(self.logfile,i)
                    j.system.platform.screen.logWindow(self.domain,name,logfile)

        else:
            if j.system.fs.exists(path="/etc/my_init.d"):
                #docker
                pass
            else:
                j.system.platform.ubuntu.startService(self.name)

        isrunning=self.isRunning(wait=True)

        if isrunning==False:
            log=self.getStartupLog().strip()

            msg=""

            if self.ports!=[]:
                ports=",".join(self.ports)
                if self.portCheck(wait=False)==False:
                    msg="Could not start, could not connect to ports %s."%(ports)

            if msg=="":
                pids=self.getPids(ifNoPidFail=False,wait=False)
                if len(pids) != self.numprocesses:
                    msg="Could not start, did not find enough running instances, needed %s, found %s"%(self.numprocesses,len(pids))

            if msg=="" and pids!=[]:
                for pid in pids:
                    test=j.system.process.isPidAlive(pid)
                    if test==False:
                        msg="Could not start, pid:%s was not alive."%pid
            
            if log!="":                
                msg="%s\nlog:\n%s\n"%(msg,log)

            self.raiseError(msg)
            return

        if self.upstart or self.isJSapp==False:
            self.getPids()
            self.registerToRedis()

        self.log("*** STARTED ***")

    def getStartupLog(self):
        if j.system.fs.exists(self.logfile):
            content=j.system.fs.fileGetContents(self.logfile)
            return content
        else:
            content=""
        return content

    def showLogs(self, command='less -R'):
        if j.system.fs.exists(self.logfile):
            j.system.process.executeWithoutPipe("%s %s" % (command, self.logfile))
        else:
            print("No logs found for %s" % self)

    def getProcessObjects(self):
        pids=self.getPids(ifNoPidFail=False,wait=False)
        results = list()
        for pid in pids:
            results.append(j.system.process.getProcessObject(pid))
        return results

    def _getPidsFromRedis(self):
        return j.system.process.appGetPidsActive(self.procname)

    def _getPidFromPS(self):
        # if 'redis' in self.cmd:
        #     port = [port for port in self.ports if port]
        #     cmd = "ps ax | grep ':%s'" % port[0]
        # else:
        # cmd="pgrep -f '%s'"%self.processfilterstr
        cmd="ps ax | grep '%s'"%self.processfilterstr
        rc,out=j.system.process.execute(cmd)
        # print cmd
        # print out

        pids=[]
        for line in out.splitlines():
            line=line.strip()
            if line.strip()=="" or line.find("grep")!=-1:
                continue
            pid=line.split(" ")[0]
            if pid.strip()!="":
                pid=int(pid)
                pids.append(pid)
        self.pids=pids
        return pids

    def getPids(self,ifNoPidFail=True,wait=False):
        #first check screen is already there with window, max waiting 1 sec        
        now=0
        pids = list()

        if wait:
            start=time.time()
            timeout=start+self.timeout
        else:
            timeout=2 #should not be 0 otherwise dont go in while loop

        if self.isJSapp:
            if not j.system.net.tcpPortConnectionTest("localhost",9999):
                return []
            while len(pids) != self.numprocesses and now<timeout:

                pids = self._getPidsFromRedis()
                if len(pids) == self.numprocesses or wait==False:
                    self.pids=pids
                    return pids
                time.sleep(0.05)
                now=time.time()
        else:
            #look at system str
            while  len(pids) != self.numprocesses and now<timeout:
                pids = self._getPidFromPS()
                if len(pids) == self.numprocesses or wait==False:
                    self.pids=pids
                    return pids
                time.sleep(0.05)
                now=time.time()

        if ifNoPidFail==False:
            self.pids=pids
            return list()

    def _portCheck(self):
        for port in self.ports:
            if port:
                if isinstance(port, str) and not port.strip():
                    continue
                port = int(port)
                if not j.system.net.checkListenPort(port):
                    return False
        return True

    def portCheck(self,wait=False):
        if wait==False:
            return self._portCheck()
        timeout=time.time()+self.timeout
        while time.time()<timeout:
            if self._portCheck():
                return True
            time.sleep(0.05)
        # print "timeout"
        return False

    def isRunning(self,wait=False):

        if self.ports!=[]:
            res= self.portCheck(wait=wait)
            return res

        pids=self.getPids(ifNoPidFail=False,wait=wait)

        if len(pids) != self.numprocesses:
            # print "numprocesses != pids"
            return False
        for pid in pids:
            test=j.system.process.isPidAlive(pid)
            if test==False:
                # print "pid not alive"
                return False
        return True

    def stop(self):
        if self.name=="redis_system":
            print("will not shut down application redis (port 9999)")
            return

        if self.upstart:
            spath="/etc/init/%s.conf"%self.name
            if j.system.fs.exists(path=spath):
                j.system.platform.ubuntu.stopService(self.name)
                if j.tools.startupmanager.upstart==False:
                    j.system.fs.remove(spath)

        pids=self.getPids(ifNoPidFail=False,wait=False)

        for pid in pids:
            if pid!=0 and j.system.process.isPidAlive(pid):
                if self.stopcmd=="":
                    print("kill:%s"%pid)
                    j.system.process.kill(pid, signal.SIGTERM)
                else:
                    j.system.process.execute(self.stopcmd)
                start=time.time()
                now=0
                while now<start+self.timeout:
                    if j.system.process.isPidAlive(pid)==False:
                        self.log("isdown:%s"%self)
                        break
                    time.sleep(0.05)
                    now=j.base.time.getTimeEpoch()
                if j.system.process.isPidAlive(pid):
                    j.system.process.kill(pid, signal.SIGKILL)

        for port in self.ports:
            if port=="" or port==None or not port.isdigit():
                self.raiseError("port cannot be none")
            j.system.process.killProcessByPort(port)

        if self.ports!=[]:
            timeout=time.time()+self.timeout
            isrunning=False            
            while time.time()<timeout:
                if self._portCheck()==False:
                    isrunning=False
                    break
                time.sleep(0.05)
            if isrunning:
                self.raiseError("Cannot stop processes on ports:%s, tried portkill"%self.ports)

        for i in range(1, self.numprocesses+1):
            name = "%s_%s" % (self.name, i)
            j.system.platform.screen.killWindow(self.domain, name)

            start=time.time()
            now=0
            windowdown=False
            while windowdown==False and now<start+2:
                if j.system.platform.screen.windowExists(self.domain, name)==False:
                    windowdown=True
                    break
                time.sleep(0.1)
                now=j.base.time.getTimeEpoch()

            if windowdown==False:
                self.raiseError("Window was not down yet within 2 sec.")

    def disable(self):
        self.stop()
        hrd=j.core.hrd.get(self.path)
        hrd.set("process.autostart",0)
        self.autostart=False

    def enable(self):
        hrd=j.core.hrd.get(self.path)
        hrd.set("process.autostart",1)
        self.autostart=True

    def restart(self):
        self.stop()
        self.start()

    def reload(self):
        if self.reload_signal and self.getProcessObject():
            self.processobject.send_signal(self.reload_signal)
        else:
            self.restart()

    def __str__(self):
        if self.system:
            s="S"
        else:
            s=" "
        if self.isJSapp:
            j="J"
        else:
            j=" "
        out="%-20s %-20s %-2s %-2s %s"%(self.domain,self.name,s,j,self.processfilterstr)
        return out

    __repr__=__str__


    __repr__ = __str__


class StartupManager:
    DEFAULT_DOMAIN = 'generic'
    LOGDIR = j.system.fs.joinPaths(j.dirs.logDir, 'startupmanager')

    def __init__(self):
        j.logger.logTargetLogForwarder=False
        
        self._configpath = j.system.fs.joinPaths(j.dirs.cfgDir, 'startup')
        j.system.fs.createDir(self._configpath)
        self.processdefs={}
        self.__init=False
        j.system.fs.createDir(StartupManager.LOGDIR)        
        self._upstart = None

    @property
    def upstart(self):
        upstartkey = "processmanager.upstart"
        if self._upstart is None:
            self._upstart = True
            if j.application.config.exists(upstartkey):
                self._upstart = j.application.config.getInt(upstartkey)==1
        return self._upstart

    def reset(self):
        self.load()
        #kill remainders
        for item in ["byobu","tmux"]:
            cmd="killall %s"%item
            j.system.process.execute(cmd,dieOnNonZeroExitCode=False)

    def installRedisSystem(self):

        for item in j.system.fs.listFilesInDir("/etc/init",filter="redis*"):
            j.system.fs.remove(item)

        for item in j.system.fs.listFilesInDir("/etc/init.d",filter="redis*"):
            j.system.fs.remove(item)

        cmd="initctl reload-configuration"
        j.system.process.execute(cmd)

        j.system.process.killProcessByName("redis-server")

        redis=j.packages.findNewest("jumpscale","redis")
        redis.instance="system"        
                   
        redis.install(reinstall=True,hrddata={"redis.name":"system","redis.port":"9999","redis.disk":"0","redis.mem":20},instance="system")
        redis.instance="system"
        redis.start()

    def _init(self):
        if self.__init==False:
            self.load()
            if not j.system.net.tcpPortConnectionTest("localhost",9999):
                j.system.process.killProcessByName("redis-server 127.0.0.1:9999")
                self.installRedisSystem()
                # try:
                #     pd = self.getProcessDef('redis', 'redis_system', True)
                # except KeyError:
                #     self.installRedisSystem()
                #     # raise RuntimeError("Redis system is not installed. Please install via 'jpackage install -n base'")
                # with j.logger.nostdout():
                #     pd.start()
                j.application.connectRedis()

            self.__init=True

    def addProcess(self, name, cmd, args="", env={}, numprocesses=1, priority=100, shell=False,\
        workingdir='',jpackage=None,domain="",ports=[],autostart=True, reload_signal=0,user="root", stopcmd=None, pid=0,\
         active=False,check=True,timeoutcheck=10,isJSapp=1,upstart=False,processfilterstr="",stats=False,log=True):
        envstr=""
        for key in list(env.keys()):
            envstr+="%s:%s,"%(key,env[key])
        envstr=envstr.rstrip(",")

        hrd="process.name=%s\n"%name
        if not domain:
            if jpackage:
                domain = jpackage.domain
            else:
                raise RuntimeError("domain should be specified or in jpackage or as argument to addProcess method.")

        hrd+="process.domain=%s\n"%domain
        hrd+="process.cmd=%s\n"%cmd
        if stopcmd:
            hrd+="process.stopcmd=%s\n"%stopcmd
        hrd+="process.args=%s\n"%args
        hrd+="process.env=%s\n"%envstr
        hrd+="process.numprocesses=%s\n"%numprocesses
        hrd+="process.reloadsignal=%s\n"%reload_signal
        hrd+="process.priority=%s\n"%priority
        hrd+="process.workingdir=%s\n"%workingdir
        hrd+="process.user=%s\n"%user
        hrd+="process.processfilterstr=%s\n"%processfilterstr
        
        if isJSapp:
            isJSapp=1
        else:
            isJSapp=0
        hrd+="process.isJSapp=%s\n"%isJSapp

        if stats:
            stats=1
        else:
            stats=0
        hrd+="process.stats=%s\n"%stats

        if log:
            log=1
        else:
            log=0
        hrd+="process.log=%s\n"%log

        if upstart:
            upstart=1
        else:
            upstart=0
        hrd+="process.upstart=%s\n"%upstart

        if autostart:
            autostart=1
        hrd+="process.timeoutcheck=%s\n"%timeoutcheck
        hrd+="process.autostart=%s\n"%autostart
        if check:
            check=1
        else:
            check=0
        hrd+="process.check=%s\n"%check
        pstring=""
        ports = ports[:]
        if jpackage and jpackage.hrd.exists('jp.process.tcpports'):
            for port in jpackage.hrd.getList('jp.process.tcpports'):
                ports.append(port)
        pstring = ",".join( str(x) for x in set(ports) )

        hrd+="process.ports=%s\n"%pstring
        if jpackage==None:
            hrd+="process.jpackage.domain=\n"
            hrd+="process.jpackage.name=\n"
            hrd+="process.jpackage.instance=\n"
            hrd+="process.jpackage.version=\n"
        else:
            hrd+="process.jpackage.domain=%s\n"%jpackage.domain
            hrd+="process.jpackage.name=%s\n"%jpackage.name
            hrd+="process.jpackage.instance=%s\n"%jpackage.instance
            hrd+="process.jpackage.version=%s\n"%jpackage.version

        j.system.fs.writeFile(filename=self._getHRDPath(domain, name),contents=hrd)

        self.load()
        pd = self.getProcessDef(domain, name, True)

        self._upstartDel(domain,name)

        if pd.upstart:
            if j.system.fs.exists(path="/etc/my_init.d"):
                #we are in docker
                cmdfile="""#!/bin/sh
exec $cmd >>/var/log/$name.log 2>&1
"""
                cmdfile=cmdfile.replace("$name","%s_%s"%(domain,name))
                cmdfile=cmdfile.replace("$cmd","%s %s"%(cmd,args))
                # nname="%s_%s"%(domain,name)
                ppath="/etc/service/%s/run"%name
                j.system.fs.createDir("/etc/service/%s"%name)
                j.system.fs.writeFile(filename=ppath,contents=cmdfile)
                j.system.fs.chmod(ppath,0o700)
                time.sleep(2)
            else:
                j.system.platform.ubuntu.serviceInstall(pd.name, pd.cmd, pd.args, pwd=pd.workingdir,env=pd.env,reload=True)

        return pd

    def _upstartDel(self,domain,name):
        pd= self.getProcessDef(domain,name,True)
        for name in [pd.name,pd.procname]:
            for item in j.system.fs.listFilesInDir("/etc/init.d"):
                itembase=j.system.fs.getBaseName(item)
                if itembase.lower() == name:
                    #found process in init.d
                    j.system.process.execute("/etc/init.d/%s stop"%itembase,dieOnNonZeroExitCode=False, outputToStdout=False)
                    j.system.fs.remove(item)

            for item in j.system.fs.listFilesInDir("/etc/init"):
                itembase=j.system.fs.getBaseName(item)
                if itembase.lower() == name:
                    #found process in init
                    itembase=itembase.replace(".conf","")
                    j.system.process.execute("sudo stop %s"%itembase,dieOnNonZeroExitCode=False, outputToStdout=False)
                    j.system.fs.remove(item)

    def _getKey(self,domain,name):
        return "%s__%s"%(domain,name)

    def _getHRDPath(self, domain, name):
        return j.system.fs.joinPaths(self._configpath ,"%s.hrd"%(self._getKey(domain,name)))

    def load(self):
        self.processdefs={}
        for path in j.system.fs.listFilesInDir(self._configpath , recursive=False,filter="*.hrd"):
            domain,name=j.system.fs.getBaseName(path).replace(".hrd","").split("__")
            key=self._getKey(domain,name)
            self.processdefs[key]=ProcessDef(j.core.hrd.get(path),path=path)

    def getProcessDef(self,domain,name, fromkey=False):
        if domain and name and fromkey:
            key = self._getKey(domain, name)
            return self.processdefs[key]
        pds=self.getProcessDefs(domain,name)
        if len(pds)>1:
            raise RuntimeError("Found more than 1 process def for %s:%s"%(domain,name))
        if len(pds)==0:
            raise RuntimeError("Could not find process def for %s:%s"%(domain,name))
        return pds[0]

    def getProcessDefs(self,domain=None,name=None,system=False):
        if self.__init==False:
            self._init()
        def processFilter(process):
            if domain and process.domain != domain:
                return False
            if name and process.name != name:
                return False
            return True

        processes = list(filter(processFilter, list(self.processdefs.values())))

        if not processes and (domain or name ):
            raise ProcessNotFoundException("Could not find process with domain:%s and name:%s" % (domain, name))

        if system:

            names=[item.procname for item in processes]

            for sname,spids in j.system.process.appsGet().items():
                if sname not in names:
                    processes.append(ProcessDefEmpty(sname))

        processes.sort(key=lambda pd: pd.priority)
            
        return processes

    def exists(self,domain=None,name=None):
        if len(self.getProcessDefs(domain,name))>0:
            return True
        return False

    def getDomains(self):
        result=[]
        for pd in self.processdefs.values():
            if pd.domain not in result:
                result.append(pd.domain)
        return result

    def startJPackage(self,jpackage):        
        for pd in self.getProcessDefs4JPackage(jpackage):
            pd.start()

    def stopJPackage(self,jpackage):        
        for pd in self.getProcessDefs4JPackage(jpackage):
            print("stop:%s"%pd)
            pd.stop()

    def existsJPackage(self,jpackage):
        return len(self.getProcessDefs4JPackage(jpackage))>0

    def getProcessDefs4JPackage(self,jpackage):
        result=[]
        
        for pd in self.getProcessDefs():
            if pd.jpackage_name==jpackage.name and pd.jpackage_domain==jpackage.domain:
                #@todo this is bug need to fix (despiegk)
                # if jpackage.instance != None:
                #     if pd.jpackage_instance==jpackage.instance:
                #         result.append(pd)
                # else:
                result.append(pd)

        if len(result)>1:
            result=[item for item in result if item.jpackage_domain==jpackage.domain]

        return result

    def startAll(self):
        l=self.getProcessDefs()
        for item in l:
            print("will start: %s %s"%(item.priority,item.name))
        
        for pd in self.getProcessDefs():
            # pd.start()
            errors=[]
            
            try:
                pd.start()
            except Exception as e:                
                errors.append("could not start: %s."%pd)
                j.errorconditionhandler.processPythonExceptionObject(e)

        if len(errors)>0:
            print("COULD NOT START:")
            print("\n".join(errors))

    def restartAll(self):
        for pd in self.getProcessDefs():
            if pd.autostart:
                pd.stop()
                pd.start()

    def removeProcess(self,domain, name):
        self.stopProcess(domain, name)
        self._upstartDel(domain,name)
        servercfg = self._getHRDPath(domain, name)
        if j.system.fs.exists(servercfg):
            j.system.fs.remove(servercfg)
        self.load()

    def remove4JPackage(self,jpackage):
        for pd in self.getProcessDefs4JPackage(jpackage):
            self.removeProcess(pd.domain,pd.name)

    def getStatus4JPackage(self,jpackage):
        result=True
        
        for pd in self.getProcessDefs4JPackage(jpackage):
            result=result and self.getStatus(pd.domain,pd.name)                
        return result

    def getStatus(self, domain, name):
        """
        get status of process, True if status ok
        """
        result=True        
        for processdef in self.getProcessDefs(domain, name):            
            result=result & processdef.isRunning()
     
        return result

    def listProcesses(self):
        files = j.system.fs.listFilesInDir(self._configpath, filter='*.hrd')
        result = list()
        for file_ in files:
            file_ = j.system.fs.getBaseName(file_)
            file_ = os.path.splitext(file_)[0]
            result.append(file_)
        return result

    def startProcess(self, domain, name):
        for pd in self.getProcessDefs(domain, name):
            pd.start()

    def stopProcess(self, domain,name):
        for pd in self.getProcessDefs(domain, name):
            pd.stop()

    def disableProcess(self, domain,name):
        for pd in self.getProcessDefs(domain, name):
            pd.disable()

    def enableProcess(self, domain,name):
        for pd in self.getProcessDefs(domain, name):
            pd.enable()

    def monitorProcess(self, domain,name):
        for pd in self.getProcessDefs(domain, name):
            pd.monitor()

    def restartProcess(self, domain,name):
        self.stopProcess(domain, name)
        self.startProcess(domain, name)

    def reloadProcess(self, domain, name):
        for pd in self.getProcessDefs(domain, name):
            pd.reload()

