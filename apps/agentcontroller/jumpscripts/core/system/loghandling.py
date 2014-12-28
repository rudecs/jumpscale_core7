from JumpScale import j

descr = """
process logs queued in redis
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "log.handling.init"
period = 5  # always in sec
startatboot = True
order = 1
enable = True
async = True
queue ='process'
log = False
roles = []

try:
    import ujson as json
except:
    import json

import time
import JumpScale.baselib.redis
import JumpScale.grid.osis

REDISIP = '127.0.0.1'
REDISPORT = 9999


def action():

    redisqueue = j.clients.credis.getRedisQueue("127.0.0.1", 9999, "logs")
    redisqueueEco = j.clients.credis.getRedisQueue("127.0.0.1", 9999, "eco")
    redisEco = j.clients.credis.getRedisClient("127.0.0.1", 9999, "eco")

    OSISclient = j.core.osis.client

    OSISclientLogger = j.core.osis.getClientForCategory(OSISclient, "system", "log")
    OSISclientEco = j.core.osis.getClientForCategory(OSISclient, "system", "eco")

    log = None
    path = "%s/apps/processmanager/loghandling/"%j.dirs.baseDir
    if j.system.fs.exists(path=path):
        loghandlingTE = j.core.taskletengine.get(path)
        log=redisqueue.get_nowait()
        # j.core.grid.logger.osis = OSISclientLogger
    else:
        loghandlingTE = None

    ecoguid = None
    path = "%s/apps/processmanager/eventhandling"%j.dirs.baseDir
    if j.system.fs.exists(path=path):
        eventhandlingTE = j.core.taskletengine.get(path)
        ecoguid=redisqueueEco.get_nowait()
    else:
        eventhandlingTE = None

    out=[]
    while log<>None:
        log2=json.decode(log)
        log3 = j.logger.getLogObjectFromDict(log2)
        log4= loghandlingTE.executeV2(logobj=log3)      
        if log4<>None:
            out.append(log4.__dict__)
        if len(out)>500:
            OSISclientLogger.set(out)
            out=[]
        log=redisqueue.get_nowait()
    if len(out)>0:
        OSISclientLogger.set(out)

    while ecoguid<>None:
        eco = json.loads(redisEco.hget('eco:objects', ecoguid))
        if not eco.get('epoch'):
            eco["epoch"] = int(time.time())
        ecoobj = j.errorconditionhandler.getErrorConditionObject(ddict=eco)        
        ecores= eventhandlingTE.executeV2(eco=ecoobj)
        if hasattr(ecores,"tb"):
            ecores.__dict__.pop("tb")        
        OSISclientEco.set(ecores.__dict__)
        ecoguid=redisqueueEco.get_nowait()

if __name__ == '__main__':
    j.core.osis.client = j.core.osis.getClientByInstance('main')
    action()
