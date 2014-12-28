from JumpScale import j

descr = """
check timeout jobs
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "system.check.job.timeout"
period = 10
enable=True
async=True
roles = []
queue ='process'
log=False

def action():
    import JumpScale.baselib.redisworker
    """
    walk over all jobs in queue & not in queue, check that timeout is not expired, if expired, put job in failed mode 
    if job failed and on queue, remove put to jobs
    """
    acclient = j.clients.agentcontroller.get()
    #j.clients.redisworker.useCRedis()
    jobs = j.clients.redisworker.getQueuedJobs(asWikiTable=False)
    result = list()
    for job in jobs:
        if (job['timeStart'] + job['timeout']) > j.base.time.getTimeEpoch() and job['state'] not in ('OK', 'SCHEDULED'):
            #job has timed out
            job['state'] = 'TIMEOUT'
            acclient.notifyWorkCompleted(job)

    # j.clients.redisworker.removeJobs(hoursago=12)#@todo does not work

    #@todo more logic required here for old jobs

    return result
