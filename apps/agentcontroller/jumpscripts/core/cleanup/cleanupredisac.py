
from JumpScale import j

descr = """
remove old redis cache from system
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
category = "redis.cleanup"
period = 300  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
log = False
roles = ['master']


def action():
    import time
    EXTRATIME = 120
    now = time.time()
    try:
        import ujson as json
    except:
        import json

    import JumpScale.grid.agentcontroller
    acl = j.clients.agentcontroller.get()

    rcl = j.clients.redis.getByInstanceName('system')
    for jobkey in rcl.keys('jobs:*'):
        if jobkey == 'jobs:last':
            continue
        jobs = rcl.hgetall(jobkey)
        for jobguid, jobstring in jobs.iteritems():
            job = json.loads(jobstring)
            if job['state'] in ['OK', 'ERROR', 'TIMEOUT']:
                rcl.hdel(jobkey, jobguid)
            elif job['timeStart'] + job['timeout'] + EXTRATIME < now:
                rcl.hdel(jobkey, jobguid)
                job['state'] = 'TIMEOUT'
                eco = j.errorconditionhandler.getErrorConditionObject(msg='Job timed out')
                j.errorconditionhandler.raiseOperationalCritical(eco=eco,die=False)
                eco.tb = None
                eco.jid = job['guid']
                eco.type = str(eco.type)
                job['result'] = json.dumps(eco.__dict__)
                acl.saveJob(job)

if __name__ == '__name__':
    action()
