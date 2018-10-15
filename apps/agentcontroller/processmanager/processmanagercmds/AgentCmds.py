from JumpScale import j
import JumpScale.grid.agentcontroller
import JumpScale.baselib.redisworker
import gevent
import time
from gevent import Timeout
from JumpScale.grid.serverbase import returnCodes

class AgentCmds():
    ORDER = 20

    def __init__(self,daemon=None):
        self._name="agent"

        if daemon==None:
            return
        self.daemon=daemon
        self._adminAuth=daemon._adminAuth

        self.redis = j.clients.redis.getByInstance('system')

    def _init(self):
        self.init()

    def log(self, msg):
        print "processmanager:%s" % msg

    def init(self, session=None):
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        self._killGreenLets()
        acinstance = j.application.instanceconfig.get('connections', {}).get('agentcontroller', 'main')
        config = j.clients.agentcontroller.getInstanceConfig(acinstance)
        ipaddr = tuple(addr.strip() for addr in config.pop('addr'))
        j.core.processmanager.daemon.schedule("agent", self.loop, ipaddr, config)

    def reconnect(self, acip, config):
        while True:
            try:
                client = j.clients.agentcontroller.get(acip, **config)
                client.register()
                return client
            except Exception:
                self.log("Failed to connect to agentcontroller %s" % str(acip))
                gevent.sleep(5)

    def loop(self, acip, config):
        """
        fetch work from agentcontroller & put on redis queue
        """
        client = self.reconnect(acip, config)
        gevent.sleep(2)
        self.log("start loop to fetch work")
        while True:
            try:
                try:
                    self.log("check if work")
                    job = client.getWork(transporttimeout=65)
                    if job is not None:
                        self.log("WORK FOUND: jobid:%(id)s cmd:%(cmd)s" % job)
                    elif job == -1:
                        # agentcontroller does not know us anymore lets reconnect
                        self.log("Need to reconnect cause agentcontroller does not know us")
                        client = self.reconnect(acip, config)
                        continue
                    else:
                        continue
                except Exception, e:
                    self.log('In exception %s' % e)
                    j.errorconditionhandler.processPythonExceptionObject(e)
                    client = self.reconnect(acip, config)
                    continue

                job['achost'] = client.ipaddr
                job['nid'] = j.application.whoAmI.nid
                if job["queue"]=="internal":
                    #cmd needs to be executed internally (is for proxy functionality)

                    if self.daemon.cmdsInterfaces.has_key(job["category"]):
                        job["resultcode"],returnformat,job["result"]=self.daemon.processRPC(job["cmd"], data=job["args"], returnformat="m", session=None, category=job["category"])
                        if job["resultcode"]==returnCodes.OK:
                            job["state"]="OK"
                        else:
                            job["state"]="ERROR"
                    else:
                        job["resultcode"]=returnCodes.METHOD_NOT_FOUND
                        job["state"]="ERROR"
                        job["result"]="Could not find cmd category:%s"%job["category"]
                    client.notifyWorkCompleted(job)
                    continue

                jscriptkey = "%(category)s_%(cmd)s" % job
                if jscriptkey not in  j.core.processmanager.cmds.jumpscripts.jumpscripts:
                    msg = "could not find jumpscript %s on processmanager"%jscriptkey
                    job['state'] = 'ERROR'
                    job['result'] = msg
                    client.notifyWorkCompleted(job)
                    j.events.bug_critical(msg, "jumpscript.notfound")

                jscript = j.core.processmanager.cmds.jumpscripts.jumpscripts[jscriptkey]
                if (jscript.async or job['queue']) and jscript.debug == False:
                    j.clients.redisworker.execJobAsync(job)
                else:
                    def run(localjob):
                        timeout = gevent.Timeout(localjob['timeout'])
                        timeout.start()
                        try:
                            localjob['timeStart'] = time.time()
                            status, result = jscript.execute(**localjob['args'])
                            localjob['timeStop'] = time.time()
                            localjob['state'] = 'OK' if status else 'ERROR'
                            localjob['result'] = result
                            client.notifyWorkCompleted(localjob)
                        finally:
                            timeout.cancel()
                    gevent.spawn(run, job)
            except Exception, e:
                print('Failed {}'.format(e))
                j.errorconditionhandler.processPythonExceptionObject(e)


    def _killGreenLets(self,session=None):
        """
        make sure all running greenlets stop
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)
        todelete=[]

        for key,greenlet in j.core.processmanager.daemon.greenlets.iteritems():
            if key.find("agent")==0:
                greenlet.kill()
                todelete.append(key)
        for key in todelete:
            j.core.processmanager.daemon.greenlets.pop(key)

    def checkRedisStatus(self, session=None):
        notrunning = list()
        for redisinstance in ['redisac', 'redisp', 'redisc']:
            if not j.clients.redis.getProcessPids(redisinstance):
                notrunning.append(redisinstance)
        if not notrunning:
            return True
        return notrunning

    def checkRedisSize(self, session=None):
        redisinfo = j.clients.redisworker.redis.info().split('\r\n')
        info = dict()
        for entry in redisinfo:
            if ':' in entry:
                key, value = entry.split(':')
                info[key] = value
        size = info['used_memory']
        maxsize = 50 * 1024 * 1024
        if j.basetype.float.fromString(size) < maxsize:
            return True
        return False
