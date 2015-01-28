from JumpScale import j
import JumpScale.baselib.screen
class ActionsBase():
    """
    implement methods of this class to change behaviour of lifecycle management of jpackage
    """

    def prepare(self,**args):
        """
        this gets executed before the files are downloaded & installed on approprate spots
        """
        return True

    def configure(self,**args):
        """
        this gets executed when files are installed
        this step is used to do configuration steps to the platform
        after this step the system will try to start the jpackage if anything needs to be started
        """
        return True

    def _getDomainName(self, process):
        domain=self.jp_instance.jp.domain
        if process["name"]!="":
            name=process["name"]
        else:
            name=self.jp_instance.jp.name
            if self.jp_instance.instance!="main":
                name+="__%s"%self.jp_instance.instance
        return domain, name

    def start(self,**args):
        """
        start happens because of info from main.hrd file but we can overrule this
        make sure to also call ActionBase.start(**args) in your implementation otherwise the default behaviour will not happen
        """

        def start2(process):
            cwd=process["cwd"]
            self.stop(**args)

            tcmd=process["cmd"]
            if tcmd=="jspython":
                tcmd="source %s/env.sh;jspython"%(j.dirs.baseDir)

            targs=process["args"]
            tuser=process["user"]
            if tuser=="":
                tuser="root"
            tlog=self.jp_instance.hrd.getBool("process.log",default=True)
            env=process["env"]

            startupmethod=process["startupmanager"]
            domain, name = self._getDomainName(process)

            j.do.delete(self.jp_instance.getLogPath())

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
                    j.system.platform.screen.logWindow(domain,name,self.jp_instance.getLogPath())

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
        for process in self.jp_instance.getProcessDicts():
            start2(process)

        isrunning=self.check_up_local()
        if isrunning==False:
            if j.system.fs.exists(path=self.jp_instance.getLogPath()):
                log=j.do.readFile(self.jp_instance.getLogPath()).strip()
            else:
                log=""

            msg=""

            if self.jp_instance.getTCPPorts()!=[]:
                ports=",".join([str(item) for item in self.jp_instance.getTCPPorts()])
                msg="Could not start:%s, could not connect to ports %s."%(self.jp_instance,ports)
                j.events.opserror_critical(msg,"jp.start.failed.ports")
            else:
                j.events.opserror_critical("could not start:%s"%self.jp_instance,"jp.start.failed.other")

    def stop(self,**args):
        """
        if you want a gracefull shutdown implement this method
        a uptime check will be done afterwards (local)
        return True if stop was ok, if not this step will have failed & halt will be executed.
        """
        def _stop(process):
            ports = process.get('ports', [])
            for port in ports:
                j.system.process.killProcessByPort(port)

            startupmethod=process["startupmanager"]
            domain, name = self._getDomainName(process)
            if j.system.fs.exists(path="/etc/my_init.d/%s"%name):
                j.do.execute("sv stop %s"%name,dieOnNonZeroExitCode=False, outputStdout=False,outputStderr=False, captureout=False)
            elif startupmethod=="tmux":
                for tmuxkey,tmuxname in j.system.platform.screen.getWindows(domain).items():
                    if tmuxname==name:
                        j.system.platform.screen.killWindow(domain,name)

        if self.jp_instance.jp.name == 'redis':
            j.logger.redislogging = None
            j.logger.redis = None

        for process in self.jp_instance.getProcessDicts():
            _stop(process)
        return True

    def halt(self,**args):
        """
        hard kill the app, std a linux kill is used, you can use this method to do something next to the std behaviour
        """
        def do(process):
            cwd=process["cwd"]
            for port in self.jp_instance.getTCPPorts():
                j.system.process.killProcessByPort(port)
            if not self.check_down_local(**args):
                j.system.process.killProcessByName(process["filterstr"])
            if not self.check_down_local(**args):
                j.events.opserror_critical("could not halt:%s"%self,"jpackage.halt")

        for process in self.jp_instance.getProcessDicts():
            do(process)

        return True

    def build(self,**args):
        """
        build instructions for the jpackage, make sure the builded jpackage ends up in right directory, this means where otherwise binaries would run from
        """
        pass

    def package(self,**args):
        """
        copy the files from the production location on the filesystem to the appropriate binary git repo
        """
        pass

    def check_up_local(self, wait=True, **args):
        """
        do checks to see if process(es) is (are) running.
        this happens on system where process is
        """
        def do(process):
            ports=self.jp_instance.getTCPPorts()
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
                filterstr=process["filterstr"]

                start=j.base.time.getTimeEpoch()
                now=start
                while now<=start+timeout:
                    if j.system.process.checkProcessRunning(filterstr):
                        return True
                    now=j.base.time.getTimeEpoch()
                return False

        for process in self.jp_instance.getProcessDicts():
            result=do(process)
            if result==False:
                return False
        return True

    def check_down_local(self,**args):
        """
        do checks to see if process(es) are all down
        this happens on system where process is
        return True when down
        """
        def do(process):
            if not self.jp_instance.hrd.exists("process.cwd"):
                return

            ports=self.jp_instance.getTCPPorts()

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
                filterstr=process["filterstr"]
                return j.system.process.checkProcessRunning(filterstr)==False

        for process in self.jp_instance.getProcessDicts():
            result=do(process)
            if result==False:
                return False
        return True

    def check_requirements(self,**args):
        """
        do checks if requirements are met to install this app
        e.g. can we connect to database, is this the right platform, ...
        """
        return True

    def monitor_local(self,**args):
        """
        do checks to see if all is ok locally to do with this package
        this happens on system where process is
        """
        return True

    def monitor_remote(self,**args):
        """
        do checks to see if all is ok from remote to do with this package
        this happens on system from which we install or monitor (unless if defined otherwise in hrd)
        """
        return True

    def cleanup(self,**args):
        """
        regular cleanup of env e.g. remove logfiles, ...
        is just to keep the system healthy
        """
        return True

    def data_export(self,**args):
        """
        export data of app to a central location (configured in hrd under whatever chosen params)
        return the location where to restore from (so that the restore action knows how to restore)
        we remember in $name.export the backed up events (epoch,$id,$state,$location)  $state is OK or ERROR
        """
        return False

    def data_import(self,id,**args):
        """
        import data of app to local location
        if specifies which retore to do, id corresponds with line item in the $name.export file
        """
        return False

    def uninstall(self,**args):
        """
        uninstall the apps, remove relevant files
        """
        pass

    def removedata(self,**args):
        """
        remove all data from the app (called when doing a reset)
        """
        pass

    def uninstall(self,**args):
        """
        uninstall the apps, remove relevant files
        """
        pass

    def test(self,**args):
        """
        test the jpackage on appropriate behaviour
        """
        pass

    def execute(self,**args):
        """
        execute is not relevant for each type of jpackage
        for e.g. a node.ms1 package it would mean remote some shell command on that machine
        for e.g. postgresql it would mean execute a sql query
        """
        pass
