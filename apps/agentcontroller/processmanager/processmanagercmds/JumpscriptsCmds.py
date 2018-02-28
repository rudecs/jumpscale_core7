from JumpScale import j
import gevent
import ujson
# from rq import Queue
# import JumpScale.baselib.redisworker
from JumpScale.baselib.redisworker.RedisWorker import RedisWorkerFactory
import crontab
import JumpScale.baselib.stataggregator
from JumpScale.grid.jumpscripts.JumpscriptFactory import Jumpscript

class JumpscriptsCmds():    

    def __init__(self,daemon=None):
        self.ORDER = 1
        self._name="jumpscripts"

        if daemon==None:
            return

        self.daemon=daemon
        self._adminAuth=daemon._adminAuth
        self.jumpscriptsByPeriod={}
        self.jumpscripts={}
        self.aggregator=j.system.stataggregator

        # self.lastMonitorResult=None
        self.lastMonitorTime=None

        self.redis = j.clients.redis.getByInstance("system", gevent=True)
        self.osis = j.clients.osis.getNamespace("system")

    @property
    def nodeStatus(self):
        return self.osis.node.get(j.application.whoAmI.nid).status

    def _init(self):
        self.loadJumpscripts(init=True)

    def loadJumpscripts(self, path="jumpscripts", session=None,init=False):
        print "LOAD JUMPSCRIPTS"
        if session is not None:
            self._adminAuth(session.user,session.passwd)

        self.agentcontroller_client = j.clients.agentcontroller.getByInstance()

        self.jumpscriptsByPeriod={}
        self.jumpscripts={}

        import JumpScale.grid.jumpscripts
        j.core.jumpscripts.loadFromAC(self.agentcontroller_client)

        jspath = j.system.fs.joinPaths(j.dirs.baseDir, 'apps', 'processmanager', 'jumpscripts')
        if not j.system.fs.exists(path=jspath):
            raise RuntimeError("could not find jumpscript directory:%s"%jspath)
        self._loadFromPath(jspath)

        self._killGreenLets()

        if init==False:
            self._configureScheduling()
            self._startAtBoot()

        j.core.processmanager.restartWorkers()

        return "ok"


    def _clean_periods(self, unscheduleperiods):
        """
        remove the priods specified in the unscheduleperiods list
        
        @param unscheduleperiods,, list(str) list of periods
        """
        for period in unscheduleperiods:
            loopkey = "loop%s" % period
            greenlet = j.core.processmanager.daemon.greenlets.pop(loopkey, None)
            if greenlet:
                greenlet.kill()
            self.jumpscriptsByPeriod.pop(period, None)

    def loadJumpscript(self, jumpscript, session=None):
        if session is not None:
            self._adminAuth(session.user, session.passwd)
        jumpscript = Jumpscript(ddict=jumpscript)

        unscheduleperiods = []
        for period, jumpscripts in self.jumpscriptsByPeriod.iteritems():
            if jumpscript in jumpscripts:
                jumpscripts.remove(jumpscript)
            if not jumpscripts:
                unscheduleperiods.append(period)
        
            self._clean_periods(unscheduleperiods)
        
        self._processJumpscript(jumpscript, self.startatboot)

        j.core.processmanager.reloadWorkers()
        self._configureScheduling()

    def unscheduleJumpscripts(self, name=None, category=None, session=None):
        """
        Unschedule jumpscripts  specified from the agent loaded, if no name of category is passed all jumpscripts are unscheduled
        @param name,, str name of the jumpscript to unschedule
        @param category ,, str category of jumpscipts to unschedule 
        """
        if session is not None:
            self._adminAuth(session.user,session.passwd)
        
        unscheduleperiods = []
        for _, jumpscripts in self.jumpscriptsByPeriod.iteritems():
            for jumpscript in jumpscripts[:]:
                if name == jumpscript.name or not name:
                    if category == jumpscript.category or not category:
                        jumpscripts.remove(jumpscript)
            if not jumpscripts:
                unscheduleperiods.append(period)
        
        self._clean_periods(unscheduleperiods)


    def scheduleJumpscripts(self, name=None, category=None, session=None):
        """
        Schedule the jumpscipt specified from the agent loaded
        @param name,, str name of the jumpscript to unschedule
        @param category ,, str category of jumpscipts to unschedule 
        """
        if session is not None:
            self._adminAuth(session.user,session.passwd)
        nodeStatus = self.nodeStatus
        unscheduleperiods = []
        for jumpscript in self.jumpscripts:
            if name == jumpscript.name or not name:
                if category == jumpscript.category or not category:
                    self._processJumpscript(jumpscript, self.startatboot, nodeStatus)

    def schedule(self):
        self._configureScheduling()
        self._startAtBoot()

    def _loadFromPath(self, path):
        self.startatboot = set()
        jumpscripts = self.agentcontroller_client.listJumpscripts()
        iddict = { (org, name): jsid for jsid, org, name, role in jumpscripts }
        nodeStatus = self.nodeStatus
        for jscriptpath in j.system.fs.listFilesInDir(path=path, recursive=True, filter="*.py", followSymlinks=True):
            js = Jumpscript(path=jscriptpath)
            js.id = iddict.get((js.organization, js.name))
            self._processJumpscript(js, self.startatboot, nodeStatus)

    def _processJumpscript(self, jumpscript, startatboot, nodeStatus):
        roles = set(j.core.grid.roles)
        if '*' in jumpscript.roles:
            jumpscript.roles.remove('*')
        if jumpscript.enable and (not jumpscript.roles or roles.intersection(set(jumpscript.roles))):
            organization = jumpscript.organization
            name = jumpscript.name
            self.jumpscripts["%s_%s"%(organization,name)]=jumpscript

            print "found jumpscript:%s " %("%s_%s" % (organization, name))
            # self.jumpscripts["%s_%s" % (organization, name)] = jumpscript
            if not (nodeStatus == 'MAINTENANCE' and 'monitor.healthcheck' == jumpscript.category):         
                period = jumpscript.period
                if period is not None:
                    if period:
                        if period not in self.jumpscriptsByPeriod:
                            self.jumpscriptsByPeriod[period]=set()
                        print "schedule jumpscript %s on period:%s"%(jumpscript.name,period)
                        self.jumpscriptsByPeriod[period].add(jumpscript)

            if jumpscript.startatboot:
                startatboot.add(jumpscript)

            self.redis.hset("workers:jumpscripts:id",jumpscript.id, ujson.dumps(jumpscript.getDict()))

            if jumpscript.organization<>"" and jumpscript.name<>"":
                self.redis.hset("workers:jumpscripts:name","%s__%s"%(jumpscript.organization,jumpscript.name), ujson.dumps(jumpscript.getDict()))

    ####SCHEDULING###

    def _killGreenLets(self,session=None):
        """
        make sure all running greenlets stop
        """
        if session is not None:
            self._adminAuth(session.user,session.passwd)
        todelete=[]

        for key,greenlet in j.core.processmanager.daemon.greenlets.iteritems():
            if key.find("loop")==0:
                greenlet.kill()
                todelete.append(key)
        for key in todelete:
            j.core.processmanager.daemon.greenlets.pop(key)            

    def _startAtBoot(self):
        for jumpscript in self.startatboot:
            jumpscript.execute()

    def _run(self,period=None, redisw=None):
        if period==None:
            for period in self.jumpscriptsByPeriod.keys():
                self._run(period)

        if period in self.jumpscriptsByPeriod:
            for action in self.jumpscriptsByPeriod[period]:
                action.execute(_redisw=redisw)

    def _loop(self, period):
        redisw = RedisWorkerFactory()
        if isinstance(period, basestring):
            wait = crontab.CronTab(period).next
        else:
            wait = lambda : period
        while True:
            waittime = wait()
            gevent.sleep(waittime)
            print 'Running JumpScripts with period {}'.format(period)
            self._run(period, redisw)

    def _configureScheduling(self):
        periods = j.core.processmanager.daemon.greenlets.keys()
        for period in self.jumpscriptsByPeriod.keys():
            loopkey = "loop%s" % period
            if loopkey not in periods:
                j.core.processmanager.daemon.schedule(loopkey, self._loop, period=period)
