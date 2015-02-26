from JumpScale import j
import JumpScale.baselib.screen
import os
import signal

CATEGORY = "atyourservice"

def log(msg, level=2):
    j.logger.log(msg, level=level, category=CATEGORY)

#decorator to execute an action on a remote machine
def remote(F): # F is func or method without instance
    def wrapper(actions, *args,**kwargs): # class instance in args[0] for method
        service=args[0]
        service.init()
        host=service.hrd.get("instance.host",default="")
        if host !="":
            parentNode = j.atyourservice.findParent(service,host)
            return actions.executeaction(service,actionname=F.func_name)
        else:
            return F(service, *args,**kwargs)
    return wrapper

class ActionsBase():
    """
    implement methods of this class to change behaviour of lifecycle management of service
    """

    @remote
    def prepare(self,serviceobj):
        """
        this gets executed before the files are downloaded & installed on approprate spots
        """
        return True

    @remote
    def configure(self,serviceobj):
        """
        this gets executed when files are installed
        this step is used to do configuration steps to the platform
        after this step the system will try to start the service if anything needs to be started
        """
        return True

    def _getDomainName(self, serviceobj, process):
        domain=serviceobj.domain
        if process["name"]!="":
            name=process["name"]
        else:
            name=serviceobj.name
            if serviceobj.instance!="main":
                name+="__%s"%serviceobj.instance
        return domain, name

    def init(self,serviceobj):
        """
        first function called, always called where service is hosted
        """
        return True

    @remote
    def start(self,serviceobj):
        """
        start happens because of info from main.hrd file but we can overrule this
        make sure to also call ActionBase.start(serviceobj) in your implementation otherwise the default behaviour will not happen
        """

        if serviceobj.getProcessDicts()==[]:
            return

        def start2(process):

            cwd=process["cwd"]
            args['process'] = process
            self.stop(serviceobj)

            tcmd=process["cmd"]
            if tcmd=="jspython":
                tcmd="source %s/env.sh;jspython"%(j.dirs.baseDir)

            targs=process["args"]
            tuser=process["user"]
            if tuser=="":
                tuser="root"
            tlog=serviceobj.hrd.getBool("process.log",default=True)
            env=process["env"]

            startupmethod=process["startupmanager"]
            domain, name = self._getDomainName(process)
            log("Starting %s:%s" % (domain, name))

            j.do.delete(serviceobj.getLogPath())

            if j.system.fs.exists(path="/etc/my_init.d/%s"%name):
                cmd2="%s %s"%(tcmd,targs)
                extracmds=""
                if cmd2.find(";")!=-1:
                    parts=cmd2.split(";")
                    extracmds="\n".join(parts[:-1])
                    cmd2=parts[-1]

                C="#!/bin/sh\nset -e\ncd %s\nrm -f /var/log/%s.log\n%s\nexec %s >>/var/log/%s.log 2>&1\n"%(cwd,name,extracmds,cmd2,name)
                j.do.delete("/var/log/%s.log"%name)
                j.do.createDir("/etc/service/%s"%name)
                path2="/etc/service/%s/run"%name
                j.do.writeFile(path2,C)
                j.do.chmod(path2,0o770)
                j.do.execute("sv start %s"%name,dieOnNonZeroExitCode=False, outputStdout=False,outputStderr=False, captureout=False)

            elif startupmethod=="upstart":
                raise RuntimeError("not implemented")
                spath="/etc/init/%s.conf"%name
                if j.system.fs.exists(path=spath):
                    j.system.platform.ubuntu.stopService(self.name)
                    if j.tools.startupmanager.upstart==False:
                        j.system.fs.remove(spath)
                cmd2="%s %s"%(tcmd,targs)  #@todo no support for working dir yet
                j.system.fs.writeFile(self.logfile,"start cmd:\n%s\n"%cmd2,True)#append
                j.system.process.executeIndependant(cmd2)

            elif startupmethod=="tmux":
                j.system.platform.screen.executeInScreen(domain,name,tcmd+" "+targs,cwd=cwd, env=env,user=tuser)#, newscr=True)

                if tlog:
                    j.system.platform.screen.logWindow(domain,name,serviceobj.getLogPath())

            else:
                raise RuntimeError("startup method not known:'%s'"%startupmethod)



                # if msg=="":
                #     pids=self.getPids(ifNoPidFail=False,wait=False)
                #     if len(pids) != self.numprocesses:
                #         msg="Could not start, did not find enough running instances, needed %s, found %s"%(self.numprocesses,len(pids))

                # if msg=="" and pids!=[]:
                #     for pid in pids:
                #         test=j.system.process.isPidAlive(pid)
                #         if test==False:
                #             msg="Could not start, pid:%s was not alive."%pid

                # if log!="":
                #     msg="%s\nlog:\n%s\n"%(msg,log)

                # self.raiseError(msg)
                # return

        isrunning=self.check_up_local(wait=False)
        if isrunning:
            return
        for process in serviceobj.getProcessDicts():
            start2(process)

        isrunning=self.check_up_local()
        if isrunning==False:
            if j.system.fs.exists(path=serviceobj.getLogPath()):
                logc=j.do.readFile(serviceobj.getLogPath()).strip()
            else:
                logc=""

            msg=""

            if serviceobj.getTCPPorts()==[0]:
                print 'Done ...'
            elif serviceobj.getTCPPorts()!=[]:
                ports=",".join([str(item) for item in serviceobj.getTCPPorts()])
                msg="Could not start:%s, could not connect to ports %s."%(serviceobj,ports)
                j.events.opserror_critical(msg,"service.start.failed.ports")
            else:
                j.events.opserror_critical("could not start:%s"%serviceobj,"service.start.failed.other")

    @remote
    def stop(self,serviceobj):
        """
        if you want a gracefull shutdown implement this method
        a uptime check will be done afterwards (local)
        return True if stop was ok, if not this step will have failed & halt will be executed.
        """

        if serviceobj.getProcessDicts()==[]:
            return

        def stop_process(process):
            currentpids = (os.getpid(), os.getppid())
            for pid in self.get_pids([process]):
                if pid not in currentpids :
                    j.system.process.kill(pid, signal.SIGTERM)

            startupmethod=process["startupmanager"]
            domain, name = self._getDomainName(process)
            if j.system.fs.exists(path="/etc/my_init.d/%s"%name):
                j.do.execute("sv stop %s"%name,dieOnNonZeroExitCode=False, outputStdout=False,outputStderr=False, captureout=False)
            elif startupmethod=="tmux":
                for tmuxkey,tmuxname in j.system.platform.screen.getWindows(domain).items():
                    if tmuxname==name:
                        j.system.platform.screen.killWindow(domain,name)

        if serviceobj.sername == 'redis':
            j.logger.redislogging = None
            j.logger.redis = None

        if 'process' in args:
            stop_process(args['process'])
        else:
            processes = serviceobj.getProcessDicts()
            if processes:
                log("Stopping %s" % serviceobj)
                for process in processes:
                    stop_process(process)
        return True

    @remote
    def get_pids(self, processes=None, **kwargs):
        pids = set()
        if processes is None:
            processes = serviceobj.getProcessDicts()
        for process in processes:
            for port in serviceobj.getTCPPorts(process):
                pids.update(j.system.process.getPidsByPort(port))
            if process.get('filterstr', None):
                pids.update(j.system.process.getPidsByFilter(process['filterstr']))
        return list(pids)

    @remote
    def halt(self,serviceobj):
        """
        hard kill the app, std a linux kill is used, you can use this method to do something next to the std behaviour
        """
        currentpids = (os.getpid(), os.getppid())
        for pid in self.get_pids():
            if pid not in currentpids :
                j.system.process.kill(pid, signal.SIGKILL)
        if not self.check_down_local(serviceobj):
            j.events.opserror_critical("could not halt:%s"%self,"service.halt")
        return True

    @remote
    def build(self,serviceobj):
        """
        build instructions for the service, make sure the builded service ends up in right directory, this means where otherwise binaries would run from
        """
        pass

    @remote
    def package(self,serviceobj):
        """
        copy the files from the production location on the filesystem to the appropriate binary git repo
        """
        pass

    @remote
    def check_up_local(self, serviceobj, wait=True):
        """
        do checks to see if process(es) is (are) running.
        this happens on system where process is
        """
        def do(process):
            ports=serviceobj.getTCPPorts()
            timeout=process["timeout_start"]
            if timeout==0:
                timeout=2
            if not wait:
                timeout = 0
            if len(ports)>0:

                for port in ports:
                    #need to do port checks
                    if wait:
                        if j.system.net.waitConnectionTest("localhost", port, timeout)==False:
                            return False
                    elif j.system.net.tcpPortConnectionTest('127.0.0.1', port) == False:
                            return False
            else:
                #no ports defined
                filterstr=process["filterstr"].strip()

                if filterstr=="":
                    raise RuntimeError("Process filterstr cannot be empty.")

                start=j.base.time.getTimeEpoch()
                now=start
                while now<=start+timeout:
                    if j.system.process.checkProcessRunning(filterstr):
                        return True
                    now=j.base.time.getTimeEpoch()
                return False

        for process in serviceobj.getProcessDicts():
            result=do(process)
            if result==False:
                domain, name = self._getDomainName(process)
                log("Status %s:%s not running" % (domain,name))
                return False
        log("Status %s is running" % (serviceobj))
        return True

    @remote
    def check_down_local(self,serviceobj):
        """
        do checks to see if process(es) are all down
        this happens on system where process is
        return True when down
        """
        def do(process):
            if not serviceobj.hrd.exists("process.cwd"):
                return

            ports=serviceobj.getTCPPorts()

            if len(ports)>0:
                timeout=process["timeout_stop"]
                if timeout==0:
                    timeout=2
                for port in ports:
                    #need to do port checks
                    if j.system.net.waitConnectionTestStopped("localhost", port, timeout)==False:
                        return False
            else:
                #no ports defined
                filterstr=process["filterstr"].strip()
                if filterstr=="":
                    raise RuntimeError("Process filterstr cannot be empty.")
                return j.system.process.checkProcessRunning(filterstr)==False

        for process in serviceobj.getProcessDicts():
            result=do(process)
            if result==False:
                return False
        return True

    @remote
    def check_requirements(self,serviceobj):
        """
        do checks if requirements are met to install this app
        e.g. can we connect to database, is this the right platform, ...
        """
        return True

    @remote
    def monitor_local(self,serviceobj):
        """
        do checks to see if all is ok locally to do with this service
        this happens on system where process is
        """
        return True

    def monitor_remote(self,serviceobj):
        """
        do checks to see if all is ok from remote to do with this service
        this happens on system from which we install or monitor (unless if defined otherwise in hrd)
        """
        return True

    @remote
    def cleanup(self,serviceobj):
        """
        regular cleanup of env e.g. remove logfiles, ...
        is just to keep the system healthy
        """
        return True

    @remote
    def data_export(self,serviceobj):
        """
        export data of app to a central location (configured in hrd under whatever chosen params)
        return the location where to restore from (so that the restore action knows how to restore)
        we remember in $name.export the backed up events (epoch,$id,$state,$location)  $state is OK or ERROR
        """
        return False

    @remote
    def data_import(self,id,serviceobj):
        """
        import data of app to local location
        if specifies which retore to do, id corresponds with line item in the $name.export file
        """
        return False

    @remote
    def uninstall(self,serviceobj):
        """
        uninstall the apps, remove relevant files
        """
        pass

    @remote
    def removedata(self,serviceobj):
        """
        remove all data from the app (called when doing a reset)
        """
        pass

    @remote
    def uninstall(self,serviceobj):
        """
        uninstall the apps, remove relevant files
        """
        pass

    @remote
    def test(self,serviceobj):
        """
        test the service on appropriate behaviour
        """
        pass

    def execute(self,serviceobj, cmd):
        """
        execute is not relevant for each type of service
        for e.g. a node.ms1 service it would mean remote some shell command on that machine
        for e.g. postgresql it would mean execute a sql query
        """
        ip = serviceobj.hrd.get("instance.machine.ssh.ip")
        port = serviceobj.hrd.get("instance.machine.ssh.port")
        keyname =  serviceobj.hrd.get('instance.ssh.key.name') if serviceobj.hrd.exists('instance.ssh.key.name') else None
        login = serviceobj.hrd.get('instance.ssh.user') if serviceobj.hrd.exists('instance.ssh.user') else None
        password = serviceobj.hrd.get('instance.ssh.pwd') if serviceobj.hrd.exists('instance.ssh.pwd') else None
        keyHRD = j.application.getAppInstanceHRD("sshkey",keyname) if keyname != None else None

        cl = None
        c = j.remote.cuisine
        if keyHRD !=None:
            c.fabric.env["key"] = keyHRD.get('instance.ssh.key.priv')
            cl = c.connect(ip,port)
        else:
            cl = c.connect(ip,port,password)
        cl.run(cmd)

    def upload(self,serviceobj,source,dest):
        """
        on central side only
        push configuration to service instance
        """
        keyname = serviceobj.hrd.get("instance.ssh.key.name")
        sshkeyHRD = j.application.getAppInstanceHRD("sshkey",keyname)
        sshkey = sshkeyHRD.get("instance.ssh.key.priv")

        ip = serviceobj.hrd.get("instance.machine.ssh.ip")
        port = serviceobj.hrd.get("instance.machine.ssh.port")
        dest = "%s:%s" % (ip,dest)
        self._rsync(source,dest,sshkey,port)

    def download(self,serviceobj,source,dest):
        """
        on central side only
        push configuration to service instance
        """
        keyname = serviceobj.hrd.get("instance.ssh.key.name")
        sshkeyHRD = j.application.getAppInstanceHRD("sshkey",keyname)
        sshkey = sshkeyHRD.get("instance.ssh.key.priv")

        ip = serviceobj.hrd.get("instance.machine.ssh.ip")
        port = serviceobj.hrd.get("instance.machine.ssh.port")
        source = "%s:%s" % (ip,source)
        self._rsync(source,dest,sshkey,port)

    def executeaction(self,serviceobj,actionname):
        """
        on central side only
        execute something in the service instance
        """
        # host=serviceobj.hrd.get("instance.host")
        # parentNode = j.atyourservice.findParent(serviceobj,host)
        self.upload(serviceobj,serviceobj.path,j.dirs.hrdDir)
        self.execute(serviceobj,"source /opt/jumpscale7/env.sh; ays %s -n %s -i %s --path %s"\
                            %(actionname,serviceobj.name,serviceobj.instance,j.dirs.hrdDir))

    def _rsync(self,source,dest,key,port=22):
        def generateUniq(name):
            import time
            epoch = int(time.time())
            return "%s__%s" % (epoch,name)

        print("copy %s %s" % (source,dest))
        # if not j.do.exists(source):
            # raise RuntimeError("copytree:Cannot find source:%s"%source)

        # if j.do.isDir(source):
        #     if dest[-1]!="/":
        #         dest+="/"
        #     if source[-1]!="/":
        #         source+="/"

        keyloc = "/tmp/%s" % generateUniq('id_dsa')
        j.system.fs.writeFile(keyloc,key)
        j.system.fs.chmod(keyloc,0o600)
        ssh = "-e 'ssh -i %s -p %s'" % (keyloc,port)

        destPath = dest.split(':')[1]

        verbose = "-q"
        if j.application.debug:
            verbose = "-v"
        cmd="rsync -a --rsync-path=\"mkdir -p %s && rsync\" %s %s %s %s"%(destPath,verbose,ssh,source,dest)
        print cmd
        j.do.execute(cmd)
        j.system.fs.remove(keyloc)