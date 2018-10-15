#!/usr/bin/env python
from JumpScale import j
import sys
import time
try:
    import ujson as json
except:
    import json
import psutil
import JumpScale.baselib.taskletengine
from JumpScale.baselib import cmdutils
from JumpScale.core.errorhandling.ErrorConditionObject import ErrorConditionObject

# Preload libraries
j.system.platform.psutil=psutil
# import JumpScale.baselib.graphite
import JumpScale.lib.diskmanager
import JumpScale.baselib.stataggregator
import JumpScale.grid.agentcontroller
import JumpScale.grid.osis
import JumpScale.baselib.redis
from JumpScale.baselib.redisworker.RedisWorker import RedisWorkerFactory
import JumpScale.grid.jumpscripts
import uuid
import os

RUNTIME = 24 * 3600

WORKERTIMEOUTS = {'default': 300,
                  'process': 300,
                  'io': 3600,
                  'hypervisor': 300}
DEFAULTTIMEOUT = 3600

class Worker(object):

    def __init__(self,queuename, logpath):
        self.actions={}
        self.clients = dict()
        self.acclient = None
        self.redisw = RedisWorkerFactory()
        self.workername = str(uuid.uuid4())
        self.queuename=queuename
        self.init()
        self.starttime = time.time()
        self.logpath = logpath
        self.logFile = None
        if self.logpath:
            self.logFile = open(self.logpath, 'w', 0)

    def getClient(self, job):
        ipaddr = getattr(job, 'achost', None)
        client = self.clients.get(ipaddr)
        if not client:
            if ipaddr:
                client = j.clients.agentcontroller.get(ipaddr, login='node')
                self.clients[ipaddr] = client
            else:
                if self.acclient is None:
                    self.acclient = j.clients.agentcontroller.getByInstance()
                return self.acclient
        return client

    def init(self):
        j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.tmpDir,"jumpscripts"))
        self.redisw.redis.delete("workers:action:%s"%self.queuename)

    def processAction(self, action):
        self.redisw.redis.delete("workers:action:%s"%self.queuename)
        if action == "RESTART":
            self.log("RESTART ASKED")
            j.application.stop(0, True)
            # jsagent will respawn worker

        if action=="RELOAD":
            self.log("RELOAD ASKED")
            self.actions={}

    def run(self):
        self.redisw.registerWorker(self.workername, self.queuename)
        self.log("STARTED")
        ppid = os.getppid()
        while True:
            if os.getppid() != ppid:
                # parent has changed time for us to stop
                break
            self.redisw.redis.hset("workers:heartbeat",self.queuename,int(time.time()))
            if self.starttime + RUNTIME < time.time():
                self.log("Running for %s seconds restarting" % RUNTIME)
                j.application.stop(0, True)
                # jsagent will respawn worker

            try:
                self.log("check if work")
                jtype, job = self.redisw._getWork(self.queuename, self.workername, timeout=10)
            except Exception as e:
                if str(e).find("Could not find queue to execute job")!=-1:
                    #create queue
                    self.log("could not find queue")
                else:
                    j.events.opserror("Could not get work from redis, is redis running?","workers.getwork",e)
                time.sleep(10)
                continue
            if jtype == "action":
                self.processAction(job)
                continue
            if job:
                j.application.jid=job.guid
                jskey = job.category, job.cmd
                try:
                    jscript = self.actions.get(jskey)
                    if jscript is None:
                        self.log("JSCRIPT CACHEMISS")
                        try:
                            jscript=self.redisw.getJumpscriptFromName(job.category, job.cmd)
                            if jscript is None:
                                # try to get it by id
                                if job.jscriptid:
                                    jscript = self.redisw.getJumpscriptFromId(job.jscriptid)
                                if jscript is None:
                                    msg="cannot find jumpscript with id:%s cat:%s cmd:%s" % (job.jscriptid, job.category, job.cmd)
                                    self.log("ERROR:%s"%msg)
                                    eco = j.errorconditionhandler.raiseOperationalCritical(msg, category="worker.jscript.notfound", die=False)
                                    job.result = eco.dump()
                                    job.state="ERROR"
                                    self.notifyWorkCompleted(job)
                                    continue
                            jscript.write()
                            jscript.load()
                            self.actions[jskey] = jscript

                        except Exception as e:
                            agentid=j.application.getAgentId()
                            if jscript!=None:
                                msg="could not compile jscript:%s %s_%s on agent:%s.\nError:%s"%(jscript.id,jscript.organization,jscript.name,agentid,e)
                            else:
                                msg="could not compile jscriptid:%s on agent:%s.\nError:%s"%(job.jscriptid,agentid,e)
                            eco=j.errorconditionhandler.parsePythonErrorObject(e)
                            eco.errormessage = msg
                            if jscript:
                                eco.code=jscript.source
                            eco.jid = job.guid
                            eco.category = 'workers.compilescript'
                            eco.process()
                            job.state="ERROR"
                            eco.tb = None
                            job.result=eco.__dict__
                            # j.events.bug_warning(msg,category="worker.jscript.notcompile")
                            # self.loghandler.logECO(eco)
                            self.notifyWorkCompleted(job)
                            continue

                        self.actions[job.jscriptid]=jscript

                    self.log("Job started:%s script:%s %s/%s"%(job.id, jscript.id,jscript.organization,jscript.name))

                    j.logger.enabled = job.log
                    if jscript.category == 'monitor.healthcheck':
                        job.log = True
                    job.timeStart = time.time()
                    if not jscript.timeout:
                        jscript.timeout = WORKERTIMEOUTS.get(self.queuename, DEFAULTTIMEOUT)
                    status, result = jscript.executeInWorker(**job.args)
                    self.redisw.redis.hdel("workers:inqueuetest",jscript.getKey())
                    j.logger.enabled = True
                    if status is True:
                        job.result=result
                        job.state="OK"
                        job.resultcode=0
                    else:
                        if isinstance(result, basestring):
                            job.state = result
                        else:
                            if isinstance(result, ErrorConditionObject):
                                eco = result
                            elif isinstance(result, dict):
                                eco = j.errorconditionhandler.getErrorConditionObject(ddict=result)
                            else:
                                eco = j.errorconditionhandler.getErrorConditionObject(msg="Invalid result {}".format(result))
                            agentid=j.application.getAgentId()
                            msg="Could not execute jscript:%s %s_%s on agent:%s\nError: %s"%(jscript.id,jscript.organization,jscript.name,agentid, eco.errormessage)
                            eco.errormessage = msg
                            eco.jid = job.guid
                            eco.code=jscript.source
                            eco.category = "workers.executejob"

                            if job.id<1000000:
                                eco.process()
                            else:
                                self.log(eco)
                            # j.events.bug_warning(msg,category="worker.jscript.notexecute")
                            # self.loghandler.logECO(eco)
                            if isinstance(status, basestring):
                                job.state = status
                            else:
                                job.state="ERROR"
                            eco.tb = None
                            job.result=eco.__dict__
                            job.resultcode=1

                    # ok or not ok, need to remove from queue test
                    # thisin queue test is done to now execute script multiple time
                    self.notifyWorkCompleted(job)
                finally:
                    j.application.jid = 0


    def notifyWorkCompleted(self, job):
        job.timeStop = int(time.time())

        if job.internal:
            # means is internal job
            self.redisw.redis.set("workers:jobs:%s" % job.id, json.dumps(job.__dict__), ex=60)
            self.redisw.redis.rpush("workers:return:%s" % job.id, time.time())
            self.redisw.redis.expire("workers:return:%s" % job.id, 60)
        try:
            acclient = self.getClient(job)
        except Exception as e:
            j.events.opserror("could not report job in error to agentcontroller", category='workers.errorreporting', e=e)
            return

        def reportJob():
            try:
                acclient.notifyWorkCompleted(job.__dict__)
            except Exception as e:
                j.events.opserror("could not report job in error to agentcontroller", category='workers.errorreporting', e=e)
                return

        # jumpscripts coming from AC
        if job.state != "OK":
            self.redisw.redis.expire("workers:jobs:%s" % job.id, 60)
            reportJob()
        else:
            if job.log or job.wait:
                reportJob()
            # we don't have to keep status of local job result, has been forwarded to AC
            if not job.internal:
                self.redisw.redis.delete("workers:jobs:%s" % job.id)

    def log(self, message, category='', level=5, time=None):
        if time is None:
            time = j.base.time.getLocalTimeHR()
        msg = "%s:worker:%s:%s" % (time, self.queuename, message)
        try:
            print(msg)
        except IOError:
            pass
        if self.logFile is not None:
            msg += "\n"
            self.logFile.write(msg)


if __name__ == '__main__':
    parser = cmdutils.ArgumentParser()
    parser.add_argument("-qn", '--queuename', help='Queue name', required=True)
    parser.add_argument("-i", '--instance', help='JSAgent instance', required=True)
    parser.add_argument("-lp", '--logpath', help='Logging file path', required=False, default=None)

    opts = parser.parse_args()

    j.application.instanceconfig = j.core.config.get("jsagent", opts.instance)

    j.core.osis.client = j.clients.osis.getByInstance(die=False)

    j.application.start("jumpscale:worker:%s" % opts.queuename)

    if j.application.config['grid']['id']:
        j.application.initGrid()

    j.logger.consoleloglevel = 2
    j.logger.maxlevel = 7

    worker = Worker(opts.queuename, opts.logpath)
    worker.run()
