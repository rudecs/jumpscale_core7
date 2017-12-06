from JumpScale import j
import time

descr = """
process logs queued in redis
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "log.handling.init"
period = 5  # always in sec
timeout = 4
startatboot = True
order = 1
enable = True
async = True
queue = 'process'
log = False
roles = ['node']

try:
    import ujson as json
except:
    import json


def action():

    rediscl = j.clients.redis.getByInstance("system")
    logqueue = rediscl.getQueue('logs')
    ecoqueue = rediscl.getQueue('eco')

    OSISclient = j.core.osis.client

    OSISclientLogger = j.clients.osis.getCategory(OSISclient, "system", "log")
    OSISclientEco = j.clients.osis.getCategory(OSISclient, "system", "eco")

    log = None
    path = "%s/apps/processmanager/loghandling/" % j.dirs.baseDir
    if j.system.fs.exists(path=path):
        loghandlingTE = j.core.taskletengine.get(path)
        log = logqueue.get_nowait()
        # j.core.grid.logger.osis = OSISclientLogger
    else:
        loghandlingTE = None

    ecokey = None
    path = "%s/apps/processmanager/eventhandling" % j.dirs.baseDir
    if j.system.fs.exists(path=path):
        eventhandlingTE = j.core.taskletengine.get(path)
        ecokey = ecoqueue.get_nowait()
    else:
        eventhandlingTE = None

    out = []
    while log is not None:
        log2 = json.decode(log)
        log3 = j.logger.getLogObjectFromDict(log2)
        log4 = loghandlingTE.executeV2(logobj=log3)
        if log4 is not None:
            out.append(log4.__dict__)
        if len(out) > 500:
            OSISclientLogger.set(out)
            out = []
        log = logqueue.get_nowait()
    if len(out) > 0 and j.application.debug:
        OSISclientLogger.set(out)

    def process_ecokey(ecokey):
        raweco = rediscl.hget('eco:objects', ecokey)
        eco = None
        if raweco:
            eco = json.loads(raweco)
            if not eco.get('epoch'):
                eco["epoch"] = int(time.time())
            ecoobj = j.errorconditionhandler.getErrorConditionObject(ddict=eco)
            ecores = eventhandlingTE.executeV2(eco=ecoobj)
            if hasattr(ecores, "tb"):
                ecores.__dict__.pop("tb")
            OSISclientEco.set(ecores.__dict__)
            eco_data = {}
            eco_data["occurrences"] = 0
            eco_data["epoch"] = eco["epoch"]
            eco_data["guid"] = eco["guid"]
            eco_data["lasttime"] = eco["lasttime"]
            eco_data["pushtime"] = eco["pushtime"]
            eco_data["gid"] = eco["gid"]
            eco_data["nid"] = eco["nid"]

            rediscl.hset('eco:objects', ecokey, json.dumps(eco_data))
            rediscl.srem('eco:secos', ecokey)

    while ecokey is not None:
        process_ecokey(ecokey)
        ecokey = ecoqueue.get_nowait()
    htime = rediscl.get('eco:htime') or 0
    if int(htime) < time.time() - 300:
        members = rediscl.smembers('eco:secos')
        if members:
            rediscl.srem('eco:secos', *members)
            for member in members:
                process_ecokey(member)
        rediscl.set('eco:htime', str(int(time.time())))


if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    action()
