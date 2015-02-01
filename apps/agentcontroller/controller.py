#this must be in the beginning so things are patched before ever imported by other libraries
from gevent import monkey
import gevent
monkey.patch_socket()
monkey.patch_thread()
monkey.patch_time()

from JumpScale import j
from JumpScale.baselib.cmdutils import argparse
import JumpScale.grid.geventws
import JumpScale.grid.osis
import importlib
import sys
import copy
import os
try:
    import ujson as json
except:
    import json
import time

import JumpScale.grid.jumpscripts   # To make j.core.jumpscripts available

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--instance', help="Agentcontroller instance", required=True)
opts = parser.parse_args()
j.application.instanceconfig = j.application.getAppInstanceHRD(name="agentcontroller",instance=opts.instance)

while not j.clients.redis.isRunning('system'):
    time.sleep(0.1)
    print "cannot connect to redis system, will keep on trying forever, please start redis system"

j.application.start("jumpscale:agentcontroller")
j.application.initGrid()

j.logger.consoleloglevel = 2

import JumpScale.baselib.redis
from JumpScale.grid.jumpscripts.JumpscriptFactory import Jumpscript


from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver as Observer

from base64 import b64encode

class JumpscriptHandler(FileSystemEventHandler):
    def __init__(self, agentcontroller):
        self.agentcontroller = agentcontroller

    def on_any_event(self, event):
        if event.src_path and not event.is_directory and event.src_path.endswith('.py'):
            try:
                self.agentcontroller.reloadjumpscripts()
            except:
                pass # reload failed shoudl try again next file change

class ControllerCMDS():

    def __init__(self, daemon):
        self.debug = False # set true for verbose output

        j.application.initGrid()

        self.daemon = daemon
        self.acuniquekey = j.application.getUniqueMachineId()
        self.jumpscripts = {}
        self.jumpscriptsFromKeys = {}
        self.jumpscriptsId={}

        self.osisclient = j.clients.osis.getByInstance(gevent=True)
        self.jobclient = j.clients.osis.getCategory(self.osisclient, 'system', 'job')
        self.nodeclient = j.clients.osis.getCategory(self.osisclient, 'system', 'node')
        self.jumpscriptclient = j.clients.osis.getCategory(self.osisclient, 'system', 'jumpscript')

        self.redis = j.clients.redis.getByInstance('system')
        self.roles2agents = dict()
        self.sessionsUpdateTime = dict()
        self.agents2roles = dict()

        self.start()

    def start(self):
        gevent.spawn(self._cleanScheduledJobs, 3600*24)
        observer = Observer()
        handler = JumpscriptHandler(self)
        observer.schedule(handler, "jumpscripts", recursive=True)
        observer.start()

    def _adminAuth(self,user,passwd):
        return self.nodeclient.authenticate(user, passwd)

    def authenticate(self, session):
        return False  # to make sure we dont use it

    def scheduleCmd(self,gid,nid,cmdcategory,cmdname,args={},jscriptid=None,queue="",log=True,timeout=None,roles=[],wait=False,errorreport=False, session=None): 
        """ 
        new preferred method for scheduling work
        @name is name of cmdserver method or name of jumpscript 
        """
        self._log("schedule cmd:%s_%s %s %s"%(gid,nid,cmdcategory,cmdname))
        if not nid and not roles:
            raise RuntimeError("Either nid or roles should be given")

        if session<>None: 
            self._adminAuth(session.user,session.passwd) 
            sessionid=session.id
        else:
            sessionid=None
        self._log("getjob osis client")
        job=self.jobclient.new(sessionid=sessionid,gid=gid,nid=nid,category=cmdcategory,cmd=cmdname,queue=queue,args=args,log=log,timeout=timeout,roles=roles,wait=wait,errorreport=errorreport) 
        
        self._log("redis incr for job")
        # if session<>None:
        #     # jobid=self.redis.hincrby("jobs:last",str(session.gid),1) 
        # else:
        jobid=self.redis.hincrby("jobs:last", str(gid), 1) 
        self._log("jobid found (incr done):%s"%jobid)
        job.id=int(jobid)

        if jscriptid is None and session<>None:
            action = self.getJumpscript(cmdcategory, cmdname, session=session)
            jscriptid = action.id
        job.jscriptid = jscriptid

        self._log("save 2 osis")

        saveinosis = True if nid and log else False
        jobdict = job.dump()
        self._setJob(jobdict, osis=saveinosis)
        jobs=json.dumps(jobdict)
        
        self._log("getqueue")
        role = roles[0] if roles else None
        q = self._getCmdQueue(gid=gid, nid=nid, role=role)
        self._log("put on queue")
        q.put(jobs)
        self._log("schedule done")
        return jobdict

    def _cleanScheduledJobs(self, expiretime):
        while True:
            self.cleanScheduledJobs(expiretime)
            time.sleep(3600)

    def cleanScheduledJobs(self, expiretime):
        queues = self.redis.keys('queues:commands:queue*')
        count = 0
        now = time.time()
        for qname in queues:
            jobstrings = self.redis.lrange(qname, 0, -1)
            for jobstring in jobstrings:
                job = json.loads(jobstring)
                timeout = job['timeout'] or expiretime
                if job['state'] == 'SCHEDULED' and job['timeStart'] + timeout < now:
                    self.redis.lrem(qname, jobstring)
                    count += 1
        return count

    def restartProcessmanagerWorkers(self,session=None):
        for item in self.osisclient.list("system","node"):
            gid,nid=item.split("_")
            if int(gid)==session.gid:
                cmds.scheduleCmd(gid,nid,cmdcategory="pm",jscriptid=0,cmdname="stop",args={},queue="internal",log=False,timeout=60,roles=[],session=session)

    def reloadjumpscripts(self,session=None):
        self.jumpscripts = {}
        self.jumpscriptsFromKeys = {}
        self.jumpscriptsId={}        
        self.loadJumpscripts()
        self.loadLuaJumpscripts()
        print "want processmanagers to reload js:",
        for item in self.osisclient.list("system","node"):
            gid,nid=item.split("_")
            cmds.scheduleCmd(gid,nid,cmdcategory="pm",jscriptid=0,cmdname="reloadjumpscripts",args={},queue="internal",log=False,timeout=60,roles=[],session=session)
        print "OK"            

    def restartWorkers(self,session=None):
        for item in self.osisclient.list("system","node"):
            gid,nid=item.split("_")
            if int(gid)==session.gid:
                cmds.scheduleCmd(gid,nid,cmdcategory="pm",jscriptid=0,cmdname="restartWorkers",args={},queue="internal",log=False,timeout=60,roles=[],session=session)

    def _setJob(self, job, osis=False):
        if not j.basetype.dictionary.check(job):
            raise RuntimeError("job needs to be dict")  
        # job guid needs to be unique accoress grid, structure $ac_gid _ $ac_nid _ $executor_gid _ $jobenum
        if not job['guid']:
            job["guid"]="%s_%s_%s"%(self.acuniquekey, job["gid"],job["id"])
        jobs=json.dumps(job)            
        self.redis.hset("jobs:%s"%job["gid"], job["guid"], jobs)
        if osis:
            # we need to make sure that job['result'] is always of the same type hence we serialize
            # otherwise elasticsearch will have issues
            self.saveJob(job)

    def saveJob(self, job, session=None):
        job = copy.deepcopy(job)
        if 'result' in job and not isinstance(job["result"],str):
            job['result'] = json.dumps(job['result'])
        for key in ('args', 'kwargs'):
            if key in job:
                job[key] = json.dumps(job[key])
        self.jobclient.set(job)

    def _deleteJobFromCache(self, job):
        self.redis.hdel("jobs:%s"%job["gid"], job["guid"])

    def _getJobFromRedis(self, jobguid):
        if not len(jobguid.split("_")) == 3:
            raise RuntimeError("Jobguid needs to be of format: '$acuniquekey_$gid_$jobid' ")
        gid = jobguid.split("_")[1]
        jobstring = self.redis.hget("jobs:%s" % gid, jobguid)
        if jobstring:
            return json.loads(jobstring)
        else:
            return None

    def _getCmdQueue(self, gid=None, nid=None, role=None, session=None):
        """
        is qeueue where commands are scheduled for processmanager to be picked up
        """
        if gid is None or (nid is None and not role):
            raise RuntimeError("gid or nid cannot be None")
        if session==None:
            self._log("get cmd queue NOSESSION")
        qname = role or nid
        self._log("get cmd queue for %s %s"%(gid,qname))
        queuename = "commands:queue:%s:%s" % (gid, qname)
        return self.redis.getQueue(queuename)

    def _getWorkQueue(self, session):
        rediscl = j.clients.redis.getByInstance('system')
        class MultiKeyQueue(object):
            def __init__(self, keys):
                self.keys = keys

            def get(self, timeout=None):
                data = rediscl.blpop(self.keys, timeout=timeout)
                if data:
                    return data[1]
                return None

        queues = list()
        nodeid="%s_%s"%(session.gid,session.nid)
        queues.append("queues:commands:queue:%s:%s" % (session.gid, session.nid))
        for role in self.agents2roles[nodeid]:
            queues.append("queues:commands:queue:%s:%s" % (session.gid, role))

        return MultiKeyQueue(queues)

    def _getJobQueue(self, jobguid):
        queuename = "jobqueue:%s" % jobguid
        self._log("get job queue for job:%s"%(jobguid))
        return self.redis.getQueue(queuename) #fromcache=False)c

    def _setRoles(self,roles, agent):
        for role, agents in self.roles2agents.iteritems():
            if agent in agents:
                agents.remove(agent)
        for role in roles:
            self.roles2agents.setdefault(role, list()).append(agent)

        self.agents2roles[agent] = roles

    def _updateNetInfo(self, netinfo, node):
        node.netaddr = netinfo
        node.ipaddr = list()
        for netitem in netinfo:
            if netitem['mac'] != "00:00:00:00:00:00" and netitem['ip'] and netitem['name']:
                node.ipaddr.extend(netitem['ip'])

    def registerNode(self, hostname, machineguid, session):
        # if session.user != 'root' or not self._adminAuth(session.user, session.passwd):
        #     raise RuntimeError("Only admin can register new nodes")
        node = self.nodeclient.new()
        node.roles = session.roles
        node.gid = session.gid
        node.name = hostname
        node.machineguid = machineguid
        self._updateNetInfo(session.netinfo, node)
        nodeid, new, changed = self.nodeclient.set(node)
        node = self.nodeclient.get(nodeid)
        self._setRoles(node.roles, nodeid)
        self.sessionsUpdateTime[nodeid]=j.base.time.getTimeEpoch()
        result = {'node': node.dump(), 'webdiskey': j.core.jumpscripts.secret}
        return result

    def register(self,session):
        self._log("new agent:")
        nodeid="%s_%s"%(session.gid,session.nid)
        if session.nid:
            node = self.nodeclient.get(nodeid)
            self._setRoles(node.roles, nodeid)
            self.sessionsUpdateTime[nodeid]=j.base.time.getTimeEpoch()
            self._log("register done:%s"%nodeid)
            self._updateNetInfo(session.netinfo, node)
            self.nodeclient.set(node)
            return node.dump()
        raise RuntimeError("Node is not registered properly please call registerNode.\n Session: %s" % session )

    def escalateError(self, eco, session=None):
        if isinstance(eco, dict):
            eco = j.errorconditionhandler.getErrorConditionObject(eco)
        eco.process()

    def loadLuaJumpscripts(self):
        """
        Like self.loadJumpscripts() but for Lua jumpscripts.
        """
        lua_jumpscript_path = 'luajumpscripts'
        available_jumpscripts = list()
        if j.system.fs.exists(lua_jumpscript_path):
            available_jumpscripts =\
                j.system.fs.listFilesInDir(path=lua_jumpscript_path, recursive=True, filter='*.lua', followSymlinks=True)

        for jumpscript_path in available_jumpscripts:
            jumpscript_metadata = j.core.jumpscripts.introspectLuaJumpscript(jumpscript_path)

            key = "%(organization)s_%(name)s" % {
                'organization': jumpscript_metadata.organization,
                'name': jumpscript_metadata.name
            }
            self.jumpscripts[key] = jumpscript_metadata

    def loadJumpscripts(self, path="jumpscripts", session=None):
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        for path2 in j.system.fs.listFilesInDir(path=path, recursive=True, filter="*.py", followSymlinks=True):

            if j.system.fs.getDirName(path2,True)[0]=="_": #skip dirs starting with _
                continue

            try:
                script = Jumpscript(path=path2)
            except Exception as e:
                msg="Could not load jumpscript:%s\n" % path2
                msg+="Error was:%s\n" % e
                # print msg
                j.errorconditionhandler.raiseInputError(msgpub="",message=msg,category="agentcontroller.load",tags="",die=False)
                j.application.stop()
                continue

            name = getattr(script, 'name', "")
            if name=="":
                name=j.system.fs.getBaseName(path2)
                name=name.replace(".py","").lower()

            t=self.jumpscriptclient.new(name=name, action=script.module.action)
            t.__dict__.update(script.getDict())

            guid,r,r=self.jumpscriptclient.set(t)
            t=self.jumpscriptclient.get(guid)
            
            self._log("found jumpscript:%s " %("id:%s %s_%s" % (t.id,t.organization, t.name)))

            key0 = "%s_%s" % (t.gid,t.id)
            key = "%s_%s" % (t.organization, t.name)
            self.jumpscripts[key] = t
            self.jumpscriptsId[key0] = t

    def getJumpscript(self, organization, name,gid=None,reload=False, session=None):
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        if gid==None and session <> None:
            gid = session.gid

        key = "%s_%s" % (organization, name)

        if key in self.jumpscripts:
            if reload:
                # from IPython import embed
                # print "DEBUG NOW getJumpscript reload"
                # embed()
                pass
            else:                
                return self.jumpscripts[key]
        else:
            j.errorconditionhandler.raiseOperationalCritical("Cannot find jumpscript %s:%s" % (organization, name), category="action.notfound", die=False)
            return ""

    def getJumpscriptFromId(self,id,gid=None,session=None):
        if session<>None:
            self._adminAuth(session.user,session.passwd)
        if gid==None and session <> None:
            gid = session.gid

        key = "%s_%s" % (gid,id)
        
        if key in self.jumpscriptsId:
            return self.jumpscriptsId[key]
        else:
            j.errorconditionhandler.raiseOperationalCritical("Cannot find jumpscript %s" % (key), category="action.notfound", die=False)

    def existsJumpscript(self, organization, name,gid=None, session=None):
        if session<>None:
            self._adminAuth(session.user,session.passwd)
            gid = session.gid

        key = "%s_%s_%s" % (gid,organization, name)
        if key in self.jumpscripts:
            return self.jumpscripts[key]
        else:
            j.errorconditionhandler.raiseOperationalCritical("Cannot find jumpscript %s:%s" % (organization, name), category="action.notfound", die=False)

    def listJumpscripts(self, organization=None, cat=None, session=None):
        """
        @return [[org,name,category,descr],...]
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        def myfilter(entry):
            if organization and entry.organization != organization:
                return False
            if cat and entry.category != cat:
                return False
            return True
        return [[t.id,t.organization, t.name] for t in filter(myfilter, self.jumpscripts.values()) ]

    def executeJumpscript(self, organization, name, nid=None, role=None, args={},all=False, \
        timeout=600,wait=True,queue="", gid=None,errorreport=True, session=None):
        """
        @param roles defines which of the agents which need to execute this action
        @all if False will be executed only once by the first found agent, if True will be executed by all matched agents
        """
        # validate params
        if not nid and not gid and not role:
            j.events.inputerror_critical("executeJumpscript requires either nid and gid or role")
        def noWork():
            sessionid = session.id
            ngid = gid or j.application.whoAmI.gid
            job=self.jobclient.new(sessionid=sessionid,gid=ngid,nid=nid,category=organization,cmd=name,queue=queue,args=args,log=True,timeout=timeout,roles=[role],wait=wait,errorreport=errorreport)
            self._log("nothingtodo")
            job.state="NOWORK"
            job.timeStop=job.timeStart
            self._setJob(job.__dict__, osis=True)
            return job.__dict__

        self._adminAuth(session.user,session.passwd)
        self._log("AC:get request to exec JS:%s %s on node:%s"%(organization,name,nid))
        action = self.getJumpscript(organization, name, session=session)
        if action==None or str(action).strip()=="":
            raise RuntimeError("Cannot find jumpscript %s %s"%(organization,name))
        if not queue:
            queue = action.queue
        if role<>None:
            self._log("ROLE NOT NONE")
            role = role.lower()
            if role in self.roles2agents:
                if not all:
                    job=self.scheduleCmd(gid,nid,organization,name,args=args,queue=queue,log=action.log,timeout=timeout,roles=[role],session=session,jscriptid=action.id, wait=wait)
                    if wait:
                        return self.waitJumpscript(job=job,session=session)
                else:
                    job = list()
                    for node_guid in self.roles2agents[role]:
                        if len(node_guid.split("_"))<>2:
                            raise RuntimeError("node_guid needs to be of format: '$gid_$nid' ")
                        ngid,nid=node_guid.split("_")
                        if gid is None or int(gid) == int(ngid):
                            jobd=self.scheduleCmd(gid=ngid,nid=nid,cmdcategory=organization,cmdname=name,args=args,queue=queue,log=action.log,timeout=timeout,roles=[role],session=session,jscriptid=action.id, wait=wait,errorreport=errorreport)
                            job.append(jobd)
                    if wait:
                        results = list()
                        for jobitem in job:
                            results.append(self.waitJumpscript(job=jobitem,session=session))
                        return results
            return noWork()
        elif nid<>None:
            self._log("NID KNOWN")
            gid = gid or session.gid
            job=self.scheduleCmd(gid,nid,organization,name,args=args,queue=queue,log=action.log,timeout=timeout,session=session,jscriptid=action.id,wait=wait)
            if wait:
                return self.waitJumpscript(job=job,session=session)
            return job
        else:
            return noWork()

    def waitJumpscript(self,jobguid=None,job=None, timeout=None, session=None):
        """
        @param timeout: if given overules job.timeout makes it possible to wait for 0 seconds
        @type timeout: int
        @return job as dict
        """
        if job==None:
            if jobguid==None:
                raise RuntimeError("job or jobid need to be given as argument")
            job = self._getJobFromRedis(jobguid)
            if not job:
                # job = self.jobclient.get(jobguid).__dict__
                # job['result'] = json.loads(job['result'])
                raise RuntimeError("Cannot find job in redis.")
        if job['state'] != 'SCHEDULED':
            return job
        q = self._getJobQueue(job["guid"])
        if timeout is None:
            timeout = job['timeout']
        if timeout == 0:
            res = q.fetch(False)
        elif timeout is not None:
            res = q.fetch(timeout=timeout)
        else:
            res = q.fetch()
        self._deleteJobFromCache(job)
        q.set_expire(5)  #@todo ????
        if res<>None:
            return json.loads(res)
        else:
            job["resultcode"]=1
            job["state"]="TIMEOUT"
            if job['nid'] is None:
                job['nid'] = 0
            else:
                self._deletelJobFromQueue(job)

            self._setJob(job, osis=True)
            self._log("timeout on execution")
            return job

    def _deletelJobFromQueue(self, job):
        cmdqueue = self._getCmdQueue(job['gid'], job['nid'])
        for jobqueue in self.redis.lrange(cmdqueue.key, 0, -1):
            qjob = json.loads(jobqueue)
            if qjob['guid'] == job['guid']:
                self.redis.lrem(cmdqueue.key, jobqueue)
                return

    def getWork(self, session=None):
        """
        is for agent to ask for work
        returns job as dict
        """
        nodeid = "%s_%s" % (session.gid, session.nid)
        self.sessionsUpdateTime[nodeid]=j.base.time.getTimeEpoch()
        self._log("getwork %s" % session)
        q = self._getWorkQueue(session)
        jobstr=q.get(timeout=30)
        if jobstr==None:
            self._log("NO WORK")
            return None
        job=json.loads(jobstr)
        if job<>None:
            job['nid'] = session.nid
            saveinosis = job['log']
            job['state'] = 'STARTED'
            self._setJob(job, saveinosis)
            self._log("getwork found for node:%s for jsid:%s"%(session.nid,job["jscriptid"]))
            return job

    def notifyWorkCompleted(self, job,session=None):
        """
        job here is a dict
        """
        self._log("NOTIFY WORK COMPLETED: jobid:%s"%job["id"])
        if not j.basetype.dictionary.check(job):
            raise RuntimeError("job needs to be dict")            
        saveinosis = job['log'] or job['state'] != 'OK'
        self._setJob(job, osis=saveinosis)
        if job['wait']:
            q=self._getJobQueue(job["guid"])
            q.put(json.dumps(job))
            q.set_expire(60) # if result is not fetched in 60 seconds we can delete this
        else:
            self._deleteJobFromCache(job)

        #NO PARENT SUPPORT YET
        # #now need to return it to the client who asked for the work 
        # if job.parent and job.parent in self.jobs:
        #     parentjob = self.jobs[job.db.parent]
        #     parentjob.db.childrenActive.remove(job.id)
        #     if job.db.state == 'ERROR':
        #         parentjob.db.state = 'ERROR'
        #         parentjob.db.result = job.db.result
        #     if not parentjob.db.childrenActive:
        #         #all children executed
        #         parentjob.db.resultcode=0
        #         if parentjob.db.state != 'ERROR':
        #             parentjob.db.state = "OK"
        #         if not parentjob.db.result:
        #             parentjob.db.result = json.dumps(None)
        #         parentjob.save()
        #         parentjob.done()

        self._log("completed job")
        return

    def getScheduledWork(self,agentid,session=None):
        """
        list all work scheduled for 1 agent
        """
        raise RuntimeError("need to be implemented")
        self._adminAuth(session.user,session.passwd)
        result=[]
        for sessionid in self.agent2session[agentid]:
            if self.workqueue.has_key(sessionid):
                if len(self.workqueue[sessionid])>0:
                    result=[item.__dict__ for item in self.workqueue[sessionid]]
        return result

    def getActiveWork(self,agentid,session=None):
        """
        list all work active for 1 agent
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)
        jobs = list()
        qname = 'queues:commands:queue:%s:%s' % (session.gid, agentid)
        jobstrings = self.redis.lrange(qname, 0, -1)
        for jobstring in jobstrings:
            jobs.append(json.loads(jobstring))
        return jobs

    def getActiveJobs(self, session=None):
        queues = self.redis.keys('queues:commands:queue*')
        jobs = list()
        for qname in queues:
            jobstrings = self.redis.lrange(qname, 0, -1)
            for jobstring in jobstrings:
                job = json.loads(jobstring)
                job['acqueue'] = qname[22:]
                jobs.append(job)
        return jobs

    def log(self, logs, session=None):
        #normally not required to use on this layer
        for log in logs:
            j.logger.logTargetLogForwarder.log(log)

    def _log(self, msg):
        if self.debug:
            print msg

    def listSessions(self,session=None):
        agents = self.agents2roles.copy()
        times = self.sessionsUpdateTime.copy()
        for key, value in times.iteritems():
            times[key] = [value] + agents.get(key, list())
        return times

    def getJobInfo(self, jobguid, session=None):
        if jobguid==None:
            raise RuntimeError("job or jobid need to be given as argument")
        job = self._getJobFromRedis(jobguid)
        if not job:
            job = self.jobclient.get(jobguid).__dict__
        return job

    def listJobs(self, session=None):
        """
        list all jobs waiting for which roles, show for each role which agents should be answering
        also list jobs which are running and running in which sessions
        """
        raise RuntimeError("need to be implemented")
        result = []
        jobresult = {}

        for jobid in self.jobs.keys():
            job = self.jobs[jobid]
            jobresult['id'] = jobid
            jobresult['jsname'] = job.db.jsname
            jobresult['jsorganization'] = job.db.jsorganization
            jobresult['roles'] = job.db.roles
            # jobresult['args'] = job.db.args
            jobresult['timeout'] = job.db.timeout
            jobresult['result'] = job.db.result
            jobresult['sessionid'] = job.db.sessionid
            jobresult['jscriptid'] = job.db.jscriptid
            jobresult['children'] = job.db.children
            jobresult['childrenActive'] = job.db.childrenActive
            jobresult['parent'] = job.db.parent
            jobresult['resultcode'] = job.db.resultcode
            if self.activeJobSessions.has_key(session.id):
                jobresult["isactive"] == jobid in self.activeJobSessions[session.id]
            else:
                jobresult["isactive"] = False
            result.append(jobresult)
        return result

    def getAllJumpscripts(self, bz2_compressed=True, types=('processmanager', 'jumpscripts'), session=None):
        """
        Returns the available jumpscripts as a Base64-encoded TAR archive that is optionally compressed using bzip2.

        Args:
            bz2_compressed (boolean): If True then the returned TAR is bzip2-compressed
            types (sequence of str): A sequence of the types of jumpscripts to be packed in the returned archive.
                possible values in the sequence are 'processmanager', 'jumpscripts', and 'luajumpscripts'.
        """
        scripts_tar_content = \
            j.core.jumpscripts.getArchivedJumpscripts(bz2_compressed=bz2_compressed, types=types)
        return b64encode(scripts_tar_content)

# will reinit for testing everytime, not really needed
# j.servers.geventws.initSSL4Server("myorg", "controller1")

port = 4444
daemon = j.servers.geventws.getServer(port=port)
daemon.addCMDsInterface(ControllerCMDS, category="agent")  # pass as class not as object !!! chose category if only 1 then can leave ""

print "load processmanager cmds"
# j.system.fs.changeDir("processmanager")
import sys
sys.path.append(j.system.fs.joinPaths(j.system.fs.getcwd(),"processmanager"))
for item in j.system.fs.listFilesInDir("processmanager/processmanagercmds",filter="*.py"):
    name=j.system.fs.getBaseName(item).replace(".py","")
    if name[0]<>"_":
        module = importlib.import_module('processmanagercmds.%s' % name)
        classs = getattr(module, name)
        print "load cmds:%s"%name
        tmp=classs()
        daemon.addCMDsInterface(classs, category="processmanager_%s" % tmp._name, proxy=True)

# j.system.fs.changeDir("..")

cmds=daemon.daemon.cmdsInterfaces["agent"]
cmds.reloadjumpscripts()
# cmds.restartProcessmanagerWorkers()

daemon.start()


j.application.stop()

