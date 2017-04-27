from JumpScale import j
import JumpScale.baselib.screen
import os
import time
import signal

CATEGORY = "atyourserviceAction"

def log(msg, level=2):
    j.logger.log(msg, level=level, category=CATEGORY)

class ActionsBase():
    """
    implement methods of this class to change behaviour of lifecycle management of service
    """

    def prepare(self,serviceobj):
        """
        this gets executed before the files are downloaded & installed on approprate spots
        """
        return True

    def prepareLocal(self, serviceobj):
        """
        This function is always exectued locally, even in the case of a remote install
        this gets executed before the files are downloaded & installed on approprate spots
        """
        return True

    def configure(self,serviceobj):
        """
        this gets executed when files are installed
        this step is used to do configuration steps to the platform
        after this step the system will try to start the service if anything needs to be started
        """
        return True

    def configureLocal(self, serviceobj):
        """
        This function is always exectued locally, even in the case of a remote install
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

    def start(self,serviceobj):
        """
        start happens because of info from main.hrd file but we can overrule this
        make sure to also call ActionBase.start(serviceobj) in your implementation otherwise the default behaviour will not happen
        """
        if serviceobj.getProcessDicts()==[]:
            return

        def start2(process, nbr=None):

            cwd=process["cwd"]
            # args['process'] = process
            if nbr is None:
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
            domain, name = self._getDomainName(serviceobj, process)
            if nbr is not None:
                name = "%s.%d" % (name, i)
            log("Starting %s:%s" % (domain, name))

            j.do.delete(serviceobj.getLogPath())

            if startupmethod == 'upstart':
                # check if we are in our docker image which uses myinit instead of upstart
                if j.system.fs.exists(path="/etc/my_init.d/"):
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
                else:
                    j.system.platform.ubuntu.serviceInstall(name, tcmd, targs, pwd=cwd, env=env)
                    j.system.platform.ubuntu.startService(name)

            elif startupmethod=="tmux":
                j.system.platform.screen.executeInScreen(domain,name,tcmd+" "+targs,cwd=cwd, env=env,user=tuser)#, newscr=True)

                if tlog:
                    j.system.platform.screen.logWindow(domain,name,serviceobj.getLogPath())

            else:
                raise RuntimeError("startup method not known or disabled:'%s'"%startupmethod)



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

        isrunning=self.check_up_local(serviceobj,wait=False)
        if isrunning:
            return

        processes = serviceobj.getProcessDicts()
        for i, process in enumerate(processes):

            if "platform" in process:
                if not j.system.platformtype.checkMatch(process["platform"]):
                    continue
            if len(processes) > 1:
                start2(process, nbr=i)
            else:
                start2(process)

        isrunning=self.check_up_local(serviceobj)
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

    def stop(self, serviceobj):
        """
        if you want a gracefull shutdown implement this method
        a uptime check will be done afterwards (local)
        return True if stop was ok, if not this step will have failed & halt will be executed.
        """

        if serviceobj.getProcessDicts()==[]:
            return

        def stop_process(process, nbr=None):
            currentpids = (os.getpid(), os.getppid())
            pids = set(self.get_pids(serviceobj,[process])) - set(currentpids)
            now = time.time()
            while pids and now + 60 > time.time():
                for pid in pids:
                    j.system.process.kill(pid, signal.SIGTERM)
                pids = set(self.get_pids(serviceobj, [process])) - set(currentpids)

            startupmethod=process["startupmanager"]
            domain, name = self._getDomainName(serviceobj, process)
            if nbr is not None:
                name = "%s.%d" % (name, i)
            log("Stopping %s:%s" % (domain, name))
            if j.system.fs.exists(path="/etc/my_init.d/%s"%name):
                j.do.execute("sv stop %s"%name,dieOnNonZeroExitCode=False, outputStdout=False,outputStderr=False, captureout=False)
            elif startupmethod == "upstart":
                j.system.platform.ubuntu.stopService(name)
            elif startupmethod=="tmux":
                for tmuxkey,tmuxname in j.system.platform.screen.getWindows(domain).items():
                    if tmuxname==name:
                        j.system.platform.screen.killWindow(domain,name)

        if serviceobj.name == 'redis':
            j.logger.redislogging = None
            j.logger.redis = None

        processes = serviceobj.getProcessDicts()
        if processes:
            for i, process in enumerate(processes):
                if len(processes) > 1:
                    stop_process(process, nbr=i)
                else:
                    stop_process(process)

        return True

    def get_pids(self,serviceobj,processes=None, **kwargs):
        pids = set()
        if processes is None:
            processes = serviceobj.getProcessDicts()
        for process in processes:
            for port in serviceobj.getTCPPorts(process):
                pids.update(j.system.process.getPidsByPort(port))
            if process.get('filterstr', None):
                pids.update(j.system.process.getPidsByFilter(process['filterstr']))
        pids = filter(j.system.process.isHostProcess, pids)
        return list(pids)

    def halt(self,serviceobj):
        """
        hard kill the app, std a linux kill is used, you can use this method to do something next to the std behaviour
        """
        currentpids = (os.getpid(), os.getppid())
        for pid in self.get_pids(serviceobj):
            if pid not in currentpids :
                j.system.process.kill(pid, signal.SIGKILL)
        if not self.check_down_local(serviceobj):
            j.events.opserror_critical("could not halt:%s"%self,"service.halt")
        return True

    def build(self,serviceobj):
        """
        build instructions for the service, make sure the builded service ends up in right directory, this means where otherwise binaries would run from
        """
        pass

    def package(self,serviceobj):
        """
        copy the files from the production location on the filesystem to the appropriate binary git repo
        """
        pass

    def check_up_local(self, serviceobj, wait=True):
        """
        do checks to see if process(es) is (are) running.
        this happens on system where process is
        """
        def do(process, nbr=None):
            startupmethod = process["startupmanager"]
            if startupmethod == 'upstart':
                domain, name = self._getDomainName(serviceobj, process)
                if nbr is not None:
                    name = "%s.%d" % (name, i)
                # check if we are in our docker image which uses myinit instead of upstart
                if j.system.fs.exists(path="/etc/my_init.d/"):
                    _, res, _ = j.do.execute("sv status %s" % name, dieOnNonZeroExitCode=False,
                                             outputStdout=False, outputStderr=False, captureout=True)
                    return res.startswith('run')
                else:
                    return j.system.platform.ubuntu.statusService(name)
            else:
                ports = serviceobj.getTCPPorts()
                timeout = process["timeout_start"]
                if timeout == 0:
                    timeout = 2
                if not wait:
                    timeout = 0
                if len(ports) > 0:
                    for port in ports:
                        # need to do port checks
                        if wait:
                            if j.system.net.waitConnectionTest("localhost", port, timeout)==False:
                                return False
                        elif j.system.net.tcpPortConnectionTest('127.0.0.1', port) == False:
                                return False
                    return True
                else:
                    # no ports defined
                    filterstr=process["filterstr"].strip()

                    if filterstr=="":
                        raise RuntimeError("Process filterstr cannot be empty.")

                    if j.system.process.checkProcessRunning(filterstr):
                        return True
                    return False
        processes = serviceobj.getProcessDicts()
        for i, process in enumerate(processes):
            start = time.time()
            timeout = process["timeout_start"]
            while start + timeout > time.time():
                if len(processes) > 1:
                    result = do(process, nbr=i)
                else:
                    result = do(process)
                if result or not wait:
                    break
            else:
                domain, name = self._getDomainName(serviceobj, process)
                log("Status %s:%s not running" % (domain, name))
                return False
        log("Status %s is running" % (serviceobj))
        return True

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

    def check_requirements(self,serviceobj):
        """
        do checks if requirements are met to install this app
        e.g. can we connect to database, is this the right platform, ...
        """
        return True

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

    def cleanup(self,serviceobj):
        """
        regular cleanup of env e.g. remove logfiles, ...
        is just to keep the system healthy
        """
        return True

    def data_export(self,serviceobj):
        """
        export data of app to a central location (configured in hrd under whatever chosen params)
        return the location where to restore from (so that the restore action knows how to restore)
        we remember in $name.export the backed up events (epoch,$id,$state,$location)  $state is OK or ERROR
        """
        return False

    def data_import(self,id,serviceobj):
        """
        import data of app to local location
        if specifies which retore to do, id corresponds with line item in the $name.export file
        """
        return False

    def uninstall(self,serviceobj):
        """
        uninstall the apps, remove relevant files
        """
        pass

    def removedata(self,serviceobj):
        """
        remove all data from the app (called when doing a reset)
        """
        pass

    def uninstall(self,serviceobj):
        """
        uninstall the apps, remove relevant files
        """
        pass

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

    def upload(self,serviceobj,source,dest):
        """
        on central side only
        push configuration to service instance
        """

    def download(self,serviceobj,source,dest):
        """
        on central side only
        pull configuration from service instance
        """

    def executeaction(self, serviceobj, actionname):
        """
        on central side only
        execute something in the service instance
        """
        node = serviceobj.getProducer('node')

        if not node:
            j.events.inputerror_critical('There seems to be no producer of type node for this service.\nConsider running ays consume --category {category} --producer {your producer instance}',
                                         category='service.execute.missing.producer')

        # first look on the remote node for the default hrd path
        result = node.actions.execute(node, 'ays hrdpath')
        # by default we use the local hrd path
        destDir = j.dirs.getHrdDir()
        for l in result.splitlines():
            if l.startswith('/'):
                destDir = l

        installationPath = j.system.fs.joinPaths(destDir, '%s__%s__%s' % (serviceobj.domain, serviceobj.name, serviceobj.instance), "installed.version")
        installed = node.actions.execute(node, 'test -f %s ; echo $?' % installationPath).strip()

        installedchecksum = node.actions.execute(node, 'cat %s' % installationPath).strip() if installed == '0' else 'not installed'

        if serviceobj.hrd.get('service.installed.checksum', 'none') != installedchecksum:
            templocation = j.system.fs.joinPaths('/tmp', j.base.idgenerator.generateGUID(), '')
            node.actions.upload(node, serviceobj.path, templocation)
            node.actions.execute(node, 'ays makelocal --tolocal "%s"' % templocation)

            # TODO: Consider a way to only sync relevant files?
            node.actions.execute(node, 'rsync -a %s/ %s/ && rm -R %s/*' % (templocation, destDir, templocation))

        # execute the action of the child service througth the producer node
        cmd = "source /opt/jumpscale7/env.sh; ays %s -n %s -i %s --noremote --data '%s'"\
              % (actionname, serviceobj.name, serviceobj.instance,
                 ' '.join(['%s:%s' % (key, value) for key, value in serviceobj.args.items()]))

        # path = j.dirs.amInGitConfigRepo()
        # if path:
        #     cmd += " --path %s" % path
        if actionname == "execute" and serviceobj.cmd:
            cmd += " --cmd '%s'" % serviceobj.cmd
        node.actions.execute(node, cmd)

        # # install can insert new info into HRD, get update files from remote
        # if actionname == 'install':
        #     node.actions.download(node, serviceobj.path, serviceobj.path)
