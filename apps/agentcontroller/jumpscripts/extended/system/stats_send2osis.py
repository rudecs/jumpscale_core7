from JumpScale import j

descr = """
send all gathered statistics to carbon (backend of monitoring)
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "monitoring.send2osis.carbon"
period = 10#120 #always in sec
enable=True
async=True
queue='process'
log = False
roles = []

def action():
    statskeys = ('system', 'disk', 'nic')
    OSISclient=j.core.osis.getNamespace("system")
    allstats = dict()
    for key in statskeys:
        stats = j.system.redisstataggregator.popStats(key)
        if stats:
            allstats[key] = stats
    if allstats:
        try:
            OSISclient.stats.set(allstats)
        except Exception,e:
            j.errorconditionhandler.processPythonExceptionObject(e)
            if str(e).find("Connection refused")<>-1:
                j.events.opserror_critical("cannot forward stats to osis, there is probably no influxdb running on osis", category='processmanager.send2osis.stats')
