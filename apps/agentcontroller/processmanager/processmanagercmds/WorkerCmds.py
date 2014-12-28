from JumpScale import j
import time
import JumpScale.baselib.redisworker
try:
    import ujson as json
except:
    import json

class WorkerCmds():

    ORDER = 10

    def __init__(self,daemon=None):
        self._name="worker"
        if not daemon:
            return
        self.daemon=daemon
        self._adminAuth=daemon._adminAuth
        self.redis=j.clients.redisworker.redis

    def getQueuedJobs(self, queue="default", format="json", session=None):
        """
        @format can be json or wiki
        @queue normally we have default,io,hypervisor
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        if format == 'json':
            return j.clients.redisworker.getQueuedJobs(queue=queue, asWikiTable=False)
        else:
            return j.clients.redisworker.getQueuedJobs(queue=queue)
        
        
    def getFailedJobs(self, queue=None, hoursago=0, format='json', session=None):
        """
        @hoursago : only show failed jobs from X hours ago, if 0 then all
        @format can be json or wiki
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        if format == 'json':
            return json.dumps(j.clients.redisworker.getFailedJobs(queue=queue, hoursago=hoursago))
        else:
            return j.clients.redisworker.getFailedJobs(queue=queue, hoursago=hoursago)
        
    def getWorkersWatchdogTime(self, session=None):
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        workers2 = self.redis.hgetall("workers:watchdog")
        foundworkers={}
        for workername, timeout in zip(workers2[0::2], workers2[1::2]):    
            foundworkers[workername]=timeout
        return foundworkers

    # def stopWorkers(self, session=None):
    #     if session<>None:
    #         self._adminAuth(session.user,session.passwd)        
    #     for workername in self.getWorkersWatchdogTime().keys():
    #         self.redis.set("workers:action:%s"%workername,"STOP")

    # def reloadWorkers(self, session=None):
    #     if session<>None:
    #         self._adminAuth(session.user,session.passwd)
    #     for workername in self.getWorkersWatchdogTime().keys():
    #         self.redis.set("workers:action:%s"%workername,"RELOAD")

    def removeJobs(self, hoursago=48, failed=False, session=None):
        """
        walk over jobs, remove jobs which are older than the specified hours
        if failed = True then also remove the failed jobs
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        j.clients.redisworker.removeJobs(hoursago=hoursago, failed=failed)

    def resetQueue(self,queue="default",hoursago=0):
        """
        @param queue, if "" then all queues
        if hoursago==0 then all items in queue
        """
        pass

    def resubmitJob(self, jobid, session=None):
        """
        job which failed or had timeout, can be resubmitted to queue, so it can be executed again
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        job = j.clients.redisworker.getJob(jobid)
        j.clients.redisworker.scheduleJob(job)

    def getJob(self, jobid, session=None):
        """
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)  

        return j.clients.redisworker.getJob(jobid)

