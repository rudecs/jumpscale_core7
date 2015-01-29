from JumpScale import j
import os,sys
import atexit
import struct
# from JumpScale.core.enumerators import AppStatusType
from collections import namedtuple

try:
    import ujson as json
except ImportError:
    import json

WhoAmI = namedtuple('WhoAmI', 'gid nid pid')

#@todo Need much more protection: cannot change much of the state (e.g. dirs) once the app is running!
#@todo Need to think through - when do we update the jpidfile (e.g. only when app is started ?)
#@todo can we make this a singleton? Then need to change __init__ to avoid clearing the content
#@todo need to implement QApplication.getVar()


class Application:

    def __init__(self):
        self.state = "UNKNOWN"
        # self.state = None
        self.appname = 'starting'
        self.agentid = "starting"
        self._calledexit = False
        self.skipTraceback = False
        self.debug = True

        self.whoAmIBytestr = None
        self.whoAmI = WhoAmI(0,0,0)

        self.config = None

        self.gridInitialized=False

        self.jid=0

        if 'JSBASE' in os.environ:
            self.sandbox=True
        else:
            self.sandbox=False

        self.interactive=True

    def init(self):

        j.logger.init()

        self.initWhoAmI()

        self.connectRedis()

    def loadConfig(self):
        self.config = j.core.hrd.get(path="%s/system" % j.dirs.hrdDir)

    def connectRedis(self):
        import JumpScale.baselib.redis
        if j.clients.redis.isRunning('system'):
            self.redis = j.clients.redis.getByInstance('system')
        else:
            self.redis=None

    def initWhoAmI(self, reload=False):
        """
        when in grid:
            is gid,nid,pid
        """

        if not self.whoAmIBytestr or reload:

            if self.config != None and self.config.exists('grid.node.id'):
                nodeid = self.config.getInt("grid.node.id")
                gridid = self.config.getInt("grid.id")
                j.logger.log("gridid:%s,nodeid:%s"%(gridid, nodeid), level=3, category="application.startup")
            else:
                gridid = 0
                nodeid = 0

            self.systempid=os.getpid()

            self.whoAmI = WhoAmI(gid=gridid, nid=nodeid, pid=0)

            self.whoAmIBytestr = struct.pack("<hhh", self.whoAmI.pid, self.whoAmI.nid, self.whoAmI.gid)


    def initGrid(self):
        if not self.gridInitialized:
            import JumpScale.grid
            j.core.grid.init()
            self.gridInitialized=True
            
    def getWhoAmiStr(self):
        return "_".join([str(item) for item in self.whoAmI])

    def getAgentId(self):
        return "%s_%s"%(self.whoAmI.gid,self.whoAmI.nid)



    def start(self,name=None,appdir="."):
        '''Start the application

        You can only stop the application with return code 0 by calling
        j.Application.stop(). Don't call sys.exit yourself, don't try to run
        to end-of-script, I will find you anyway!
        '''
        if name:
            self.appname = name

        if "JSPROCNAME" in os.environ:
            self.appname=os.environ["JSPROCNAME"]

        if self.state == "RUNNING":
            raise RuntimeError("Application %s already started" % self.appname)

        # Register exit handler for sys.exit and for script termination
        atexit.register(self._exithandler)

        j.dirs.appDir=appdir

        j.dirs.init(reinit=True)

        if hasattr(self, 'config'):
            self.debug = j.application.config.getBool('system.debug', default=True)

        if self.redis!=None:
            if self.redis.hexists("application",self.appname):
                pids=json.loads(self.redis.hget("application",self.appname))
            else:
                pids=[]
            if self.systempid not in pids:
                pids.append(self.systempid)
            self.redis.hset("application",self.appname,json.dumps(pids))

        # Set state
        self.state = "RUNNING"

        # self.initWhoAmI()

        j.logger.log("***Application started***: %s" % self.appname, level=8, category="jumpscale.app")

    def stop(self, exitcode=0, stop=True):

        '''Stop the application cleanly using a given exitcode

        @param exitcode: Exit code to use
        @type exitcode: number
        '''
        import sys

        #@todo should we check the status (e.g. if application wasnt started, we shouldnt call this method)
        if self.state == "UNKNOWN":
            # Consider this a normal exit
            self.state = "HALTED"
            sys.exit(exitcode)

        # Since we call os._exit, the exithandler of IPython is not called.
        # We need it to save command history, and to clean up temp files used by
        # IPython itself.
        j.logger.log("Stopping Application %s" % self.appname, 8)
        try:
            __IPYTHON__.atexit_operations()
        except:
            pass

        # # Write exitcode
        # if self.writeExitcodeOnExit:
        #     exitcodefilename = j.system.fs.joinPaths(j.dirs.tmpDir, 'qapplication.%d.exitcode'%os.getpid())
        #     j.logger.log("Writing exitcode to %s" % exitcodefilename, 5)
        #     j.system.fs.writeFile(exitcodefilename, str(exitcode))

        # was probably done like this so we dont end up in the _exithandler
        # os._exit(exitcode) Exit to the system with status n, without calling cleanup handlers, flushing stdio buffers, etc. Availability: Unix, Windows.

        self._calledexit = True  # exit will raise an exception, this will bring us to _exithandler
                              # to remember that this is correct behaviour we set this flag

        #tell gridmaster the process stopped

        #@todo this SHOULD BE WORKING AGAIN, now processes are never removed

        # if self.gridInitialized:
        #     client=j.core.osis.getClient(user='root')            
        #     clientprocess=j.core.osis.getCategory(client,"system","process")
        #     key = "%s_%s"%(j.application.whoAmI.gid,j.application.whoAmI.pid)
        #     if clientprocess.exists(key):
        #         obj=clientprocess.get(key)
        #         obj.epochstop=j.base.time.getTimeEpoch()
        #         obj.active=False
        #         clientprocess.set(obj)
        if stop:
            sys.exit(exitcode)

    def _exithandler(self):
        # Abnormal exit
        # You can only come here if an application has been started, and if
        # an abnormal exit happened, i.e. somebody called sys.exit or the end of script was reached
        # Both are wrong! One should call j.application.stop(<exitcode>)
        #@todo can we get the line of code which called sys.exit here?
        
        #j.logger.log("UNCLEAN EXIT OF APPLICATION, SHOULD HAVE USED j.application.stop()", 4)
        import sys
        if not self._calledexit:
            self.stop(stop=False)

    def getAppInstanceHRD(self,name,instance,domain="jumpscale"):
        """
        returns hrd for specific appname & instance name (default domain=jumpscale or not used when inside a config git repo)
        """
        if j.packages.type!="c":
            path='%s/%s.%s.%s.hrd' % (j.dirs.getHrdDir(),domain,name,instance)
        else:
            path='%s/%s.%s.hrd' % (j.dirs.getHrdDir(),name,instance)
        if not j.system.fs.exists(path=path):
            j.events.inputerror_critical("Could not find hrd for app: %s/%s, please install, looked on location:%s"%(name,instance,path))
        return j.core.hrd.get(path)

    def getAppInstanceHRDs(self,name,domain="jumpscale"):
        """
        returns list of hrd instances for specified app
        """
        res=[]
        for instance in self.getAppHRDInstanceNames(name,domain):
            res.append(self.getAppInstanceHRD(name,instance,domain))
        return res

    def getAppHRDInstanceNames(self,name,domain="jumpscale"):
        """
        returns hrd instance names for specific appname (default domain=jumpscale)
        """

        names=[j.system.fs.getBaseName(item)[:-4] for item in j.system.fs.listFilesInDir(j.dirs.getHrdDir(),False)]
        res=[]
        for name1 in names:
            if j.packages.type!="c":
                if name1.startswith(domain):
                    name1=name1[len(domain)+1:]
            if name1.startswith(name):
                instance=name1[len(name)+1:]
                if instance not in res:
                    res.append(instance)
                
        res.sort()
        return res

    def getCPUUsage(self):
        """
        try to get cpu usage, if it doesn't work will return 0
        By default 0 for windows
        """
        try:
            pid = os.getpid()
            if j.system.platformtype.isWindows():
                return 0
            if j.system.platformtype.isLinux():
                command = "ps -o pcpu %d | grep -E --regex=\"[0.9]\""%pid
                j.logger.log("getCPUusage on linux with: %s" % command, 8)
                exitcode, output = j.system.process.execute(command, True, False)
                return output
            elif j.system.platformtype.isSolaris():
                command = 'ps -efo pcpu,pid |grep %d'%pid
                j.logger.log("getCPUusage on linux with: %s" % command, 8)
                exitcode, output = j.system.process.execute(command, True, False)
                cpuUsage = output.split(' ')[1]
                return cpuUsage
        except Exception:
            pass
        return 0

    def getMemoryUsage(self):
        """
        try to get memory usage, if it doesn't work will return 0i
        By default 0 for windows
        """
        try:
            pid = os.getpid()
            if j.system.platformtype.isWindows():
                # Not supported on windows
                return "0 K"
            elif j.system.platformtype.isLinux():
                command = "ps -o pmem %d | grep -E --regex=\"[0.9]\""%pid
                j.logger.log("getMemoryUsage on linux with: %s" % command, 8)
                exitcode, output = j.system.process.execute(command, True, False)
                return output
            elif j.system.platformtype.isSolaris():
                command = "ps -efo pcpu,pid |grep %d"%pid
                j.logger.log("getMemoryUsage on linux with: %s" % command, 8)
                exitcode, output = j.system.process.execute(command, True, False)
                memUsage = output.split(' ')[1]
                return memUsage
        except Exception:
            pass
        return 0

    def getUniqueMachineId(self):
        """
        will look for network interface and return a hash calculated from lowest mac address from all physical nics
        """
        # if unique machine id is set in grid.hrd, then return it
        uniquekey = 'grid.node.machineguid'
        if j.application.config.exists(uniquekey):
            machineguid = j.application.config.get(uniquekey)
            if machineguid.strip():
                return machineguid

        nics = j.system.net.getNics()
        if j.system.platformtype.isWindows():
            order = ["local area", "wifi"]
            for item in order:
                for nic in nics:
                    if nic.lower().find(item) != -1:
                        return j.system.net.getMacAddress(nic)
        macaddr = []
        for nic in nics:
            if nic.find("lo") == -1:
                nicmac = j.system.net.getMacAddress(nic)
                macaddr.append(nicmac.replace(":", ""))
        macaddr.sort()
        if len(macaddr) < 1:
            raise RuntimeError("Cannot find macaddress of nics in machine.")

        if j.application.config.exists(uniquekey):
            j.application.config.set(uniquekey, macaddr[0])
        return macaddr[0]

    def _setWriteExitcodeOnExit(self, value):
        if not j.basetype.boolean.check(value):
            raise TypeError
        self._writeExitcodeOnExit = value

    def _getWriteExitcodeOnExit(self):
        if not hasattr(self, '_writeExitcodeOnExit'):
            return False
        return self._writeExitcodeOnExit

    writeExitcodeOnExit = property(fset=_setWriteExitcodeOnExit, fget=_getWriteExitcodeOnExit, doc="Gets / sets if the exitcode has to be persisted on disk")
