from JumpScale import j
try:
    import ujson as json
except:
    import json

import JumpScale.baselib.hash
import JumpScale.grid.osis
import JumpScale.baselib.redis

import JumpScale.baselib.redis

from .Job import Job

class JobHandler(object):
    """
    """

    def __init__(self):
        self._redis=None
        self._jobToRedis=None

    def _send2Redis(self,job):
        if self._redis==None:
            if j.system.net.tcpPortConnectionTest("127.0.0.1",9999):    
                self._redis=j.clients.redis.getRedisClient("127.0.0.1",9999)
                luapath="%s/core/jobmanager/job.lua"%j.dirs.jsLibDir
                if j.system.fs.exists(path=luapath):
                    lua=j.system.fs.fileGetContents(luapath)
                    self._jobToRedis=self._redis.register_script(lua)    

        if self._redis!=None and self._jobToRedis!=None:
            job.getSetGuid()
            key=job.getUniqueKey()
            
            data=job.toJson()
            return json.decode(self._jobToRedis(keys=["job.queue","job.incr","job.objects","job.last"],args=[key,data]))
        else:
            return None


    def getJobClass(self):
        return Job

    def getJob(self,jobguid):
        jobdict=self._redis.hget("workers:jobs",jobid)
        if jobdict:
            jobdict=json.loads(jobdict)
        else:
            raise RuntimeError("cannot find job with id:%s"%jobid)
        return jobdict


    def waitJob(self,job,timeout=600):
        result=self._redis.blpop("workers:return:%s"%job.id, timeout=timeout)        
        if result==None:            
            job.state="TIMEOUT"
            job.timeStop=int(time.time())
            self._redis.hset("workers:jobs",job.id, json.dumps(job.__dict__))
            j.events.opserror("timeout on job:%s"%job, category='workers.job.wait.timeout', e=None)
        else:
            job=self.getJob(job.id)

        job=Job(ddict=job)
        if job.state!="OK":
            eco=j.errorconditionhandler.getErrorConditionObject(ddict=job.result)
            # eco.process()
            raise RuntimeError("Could not execute job, error:\n%s"%str(eco))  #@todo is printing too much
        return job

    def _scheduleJob(self, job):
        """
        """

        qname=job.queue
        if not qname or qname.strip()=="":
            qname="default"

        if qname not in self.queue:
            raise RuntimeError("Could not find queue to execute job:%s ((ops:workers.schedulework L:1))"%job)

        queue=self.queue[qname]

        # if not self.jobExistsInQueue(qname,job):
            # self._redis.hset("workers:jobs",job.id, json.dumps(job.__dict__))
        queue.put(job)


    def scheduleJob(self, job):
        jobobj = Job(ddict=job)
        self._scheduleJob(jobobj)

    def getJobLine(self,job=None,jobid=None):
        if jobid!=None:
            job=self.getJob(jobid)
        start=j.base.time.epoch2HRDateTime(job['timeStart'])
        if job['timeStop']==0:
            stop="N/A"
        else:
            stop=j.base.time.epoch2HRDateTime(job['timeStop'])
        jobid = '[%s|/grid/job?id=%s]' % (job['id'], job['id'])
        line="|%s|%s|%s|%s|%s|%s|%s|%s|" % (jobid, job['state'], job['queue'], job['category'], job['cmd'], job['jscriptid'], start, stop)
        return line


    def getQueuedJobs(self, queue=None, asWikiTable=True):
        result = list()
        queues = [queue] if queue else ["io","hypervisor","default"]
        for item in queues:
            jobs = self._redis.lrange('queues:workers:work:%s' % item, 0, -1)
            for jobstring in jobs:
                result.append(json.loads(jobstring))
        if asWikiTable:
            out=""
            for job in result:
                out+="%s\n"%self.getJobLine(job=job)
            return out
        return result

    def getFailedJobs(self, queue=None, hoursago=0):
        jobs = list()
        queues = (queue,) if queue else ('io', 'hypervisor', 'default')
        for q in queues:
            jobsjson = self._redis.lrange('queues:workers:work:%s' % q, 0, -1)
            for jobstring in jobsjson:
                jobs.append(json.loads(jobstring))

        #get failed jobs
        for job in jobs:
            if job['state'] not in ('ERROR', 'TIMEOUT'):
                jobs.remove(job)

        if hoursago:
            epochago = j.base.time.getEpochAgo(str(hoursago))
            for job in jobs:
                if job['timeStart'] <= epochago:
                    jobs.remove(job)
        return jobs

    def removeJobs(self, hoursago=48, failed=False):
        epochago = j.base.time.getEpochAgo(hoursago)
        for q in ('io', 'hypervisor', 'default'):
            jobs = dict()
            jobsjson = self._redis.hgetall('queues:workers:work:%s' % q)
            if jobsjson:
                jobs.update(json.loads(jobsjson))
                for k, job in jobs.items():
                    if job['timeStart'] >= epochago:
                        jobs.pop(k)

                if not failed:
                    for k, job in jobs.items():
                        if job['state'] in ('ERROR', 'TIMEOUT'):
                            jobs.pop(k)

                if jobs:
                    self._redis.hdel('queues:workers:work:%s' % q, list(jobs.keys()))

    def deleteJob(self, jobid):
        job = self.getJob(jobid)
        self._redis.hdel('queues:workers:work:%s' % job.queue, jobid)
