from JumpScale import j
import JumpScale.baselib.screen
class ActionsBase():
    """
    process for install
    -------------------
    step1: prepare actions
    step2: check_requirements action
    step3: download files & copy on right location (hrd info is used)
    step4: configure action
    step5: check_uptime_local to see if process stops  (uses timeout $process.stop.timeout)
    step5b: if check uptime was true will do stop action and retry the check_uptime_local check
    step5c: if check uptime was true even after stop will do halt action and retry the check_uptime_local check
    step6: use the info in the hrd to start the application
    step7: do check_uptime_local to see if process starts
    step7b: do monitor_local to see if package healthy installed & running
    step7c: do monitor_remote to see if package healthy installed & running, but this time test is done from central location
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

    def start(self,**args):
        if not self.jp_instance.hrd.exists("process.cwd"):
            return
        cwd=self.jp_instance.hrd.get("process.cwd")
        if cwd.strip()=="":
            return

        self.stop(**args)

        tcmd=self.jp_instance.hrd.get("process.cmd")
        if tcmd=="jspython":
            tcmd="source %s/env.sh;jspython"%(j.dirs.baseDir)
            

        targs=self.jp_instance.hrd.get("process.args")
        tuser=self.jp_instance.hrd.get("process.user",default="root")
        tlog=self.jp_instance.hrd.getBool("process.log",default=True)
        env=self.jp_instance.hrd.get("process.env",default="")
        domain=self.jp_instance.jp.domain
        name=self.jp_instance.jp.name
        if self.jp_instance.instance!="name":
            name+="__%s"%self.jp_instance.instance

        startupmethod=self.jp_instance.hrd.get("process.startupmanager",default="tmux")

        j.do.delete(self.jp_instance.getLogPath())

        if j.system.fs.exists(path="/etc/my_init.d"):
            j.do.execute("sv stop %s"%name,dieOnNonZeroExitCode=False, outputToStdout=False, ignoreErrorOutput=True)

            for port in [int(item) for item in self.jp_instance.hrd.getList("process.ports") if str(item).strip()<>""]:
                print ("KILL: %s (%s)"%(name,port))
                j.system.process.killProcessByPort(port)

            cmd2="%s %s"%(tcmd,targs)
            C="#!/bin/sh\nset -e\ncd %s\nrm -f /var/log/%s.log\nexec %s >>/var/log/%s.log 2>&1\n"%(cwd,name,cmd2,name)
            j.do.delete("/var/log/%s.log"%name)
            j.do.createDir("/etc/service/%s"%name)
            path2="/etc/service/%s/run"%name
            j.do.writeFile(path2,C)
            j.do.chmod(path2,0o770)            
            j.do.execute("sv start %s"%name,dieOnNonZeroExitCode=False, outputToStdout=False, ignoreErrorOutput=True)
            print "STARTED SUCCESFULLY:%s"%name
        
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

            for tmuxkey,tmuxname in j.system.platform.screen.getWindows(domain).items():
                if tmuxname==name:
                    j.system.platform.screen.killWindow(domain,name)

            #@todo need to do env            
            j.system.platform.screen.executeInScreen(domain,name,tcmd+" "+targs,cwd=cwd, env={},user=tuser)#, newscr=True)

            if tlog:
                j.system.platform.screen.logWindow(domain,name,self.jp_instance.getLogPath())

        else:
            if j.system.fs.exists(path="/etc/my_init.d"):
                #docker
                pass
            else:
                j.system.platform.ubuntu.startService(self.name)

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

    def stop(self,**args):
        """
        """
        return True

    def halt(self,**args):
        """
        hard kill the app, std a linux kill is used, you can use this method to do something next to the std behaviour
        """
        print "HARDKILL"
        for port in self.jp_instance.getTCPPorts():
            j.system.process.killProcessByPort(port)
        if not self.check_down_local(**args):
            j.system.process.killProcessByName(self.jp_instance.hrd.get("process.filterstr"))         
        if not self.check_down_local(**args):
            j.events.opserror_critical("could not halt:%s"%self,"jpackage.halt")
        return True

    def check_up_local(self,**args):
        """
        do checks to see if process(es) is (are) running.
        this happens on system where process is
        """        
        ports=self.jp_instance.getTCPPorts()
        timeout=self.jp_instance.hrd.get("process.start.timeout",default=2)
        if len(ports)>0:
            
            for port in ports:
                #need to do port checks
                if j.system.net.waitConnectionTest("localhost", port, timeout)==False:
                    
                    return False
            return True
        else:
            #no ports defined 
            filterstr=self.jp_instance.hrd.get("process.filterstr")

            start=j.base.time.getTimeEpoch()
            now=start
            while now<start+timeout:
                if j.system.process.checkProcessRunning(filterstr):
                    return True
                now=j.base.time.getTimeEpoch()
            return False
        return False

    def check_down_local(self,**args):
        """
        do checks to see if process(es) are all down
        this happens on system where process is
        return True when down
        """        
        ports=self.jp_instance.getTCPPorts()

        if len(ports)>0:
            timeout=self.jp_instance.hrd.get("process.start.timeout",default=2)
            for port in ports:
                #need to do port checks
                if j.system.net.waitConnectionTestStopped("localhost", port, timeout)==False:
                    return False
            return True
        else:
            #no ports defined 
            filterstr=self.jp_instance.hrd.get("process.filterstr")
            return j.system.process.checkProcessRunning(filterstr)==False

        return False        

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


