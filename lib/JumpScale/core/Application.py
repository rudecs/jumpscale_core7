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
        self.debug = False

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
        self.redis=None

    def init(self):
        self.initWhoAmI()

    def loadConfig(self):
        config = {}
        for instance in j.core.config.list('system'):
            config[instance] = j.core.config.get('system', instance)
        self.config = config

    def connectRedis(self):
        if j.logger.enabled:
            waittime = 60 if self.appname not in ['starting', 'jsshell', 'ays'] else 0
            if j.system.net.waitConnectionTest("localhost", 9999, timeout=waittime):
                j.logger.connectRedis()
                self.redis=j.logger.redis
                # import JumpScale.baselib.redis
                # if j.clients.redis.isRunning('system'):
                #     self.redis = j.clients.redis.getByInstance('system')
                #     return        
                return
            print "WARNING: no system redis found (port 9999, needs to be installed as instance 'system')."
            j.logger.enabled=False

    def initWhoAmI(self, reload=False):
        """
        when in grid:
            is gid,nid,pid
        """

        if not self.whoAmIBytestr or reload:
            nodeid = self.config["grid"]["node"]['id'] or 0
            gridid = self.config["grid"]['id'] or 0
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
        self.connectRedis()

        if j.logger.enabled:
            j.logger.redis=self.redis
            j.logger.init()
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
            self.debug = j.application.config['system'].get('debug', False)

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
        #     client=j.clients.osis.get(user='root')            
        #     clientprocess=j.clients.osis.getCategory(client,"system","process")
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
        # if unique machine id is set in grid.yml, then return it
        grid = j.application.config['grid']
        machineguid = grid['node']['machineguid']
        if machineguid:
            return machineguid

        gwnic, _ = j.system.net.getDefaultIPConfig()
        machineguid = j.system.net.getMacAddress(gwnic).replace(':', '')
        grid['node']['machineguid'] = machineguid
        j.core.config.set('system', 'grid', grid)
        return machineguid

    def _setWriteExitcodeOnExit(self, value):
        if not j.basetype.boolean.check(value):
            raise TypeError
        self._writeExitcodeOnExit = value

    def _getWriteExitcodeOnExit(self):
        if not hasattr(self, '_writeExitcodeOnExit'):
            return False
        return self._writeExitcodeOnExit

    writeExitcodeOnExit = property(fset=_setWriteExitcodeOnExit, fget=_getWriteExitcodeOnExit, doc="Gets / sets if the exitcode has to be persisted on disk")
