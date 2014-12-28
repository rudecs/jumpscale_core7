from JumpScale import j
import time

descr = """
Monitor Redis status
"""

organization = "jumpscale"
name = 'redis_monitoring'
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.redis"

period = 300 #always in sec
enable = False #@todo need other implementation
async = True
roles = []
log=False
queue="process"

def action():
    import JumpScale.grid.gridhealthchecker
    nodeid = j.application.whoAmI.nid

    rstatus, errors = j.core.grid.healthchecker.checkRedis(nodeid)
    for data in [rstatus, errors]:
        if len(data) > 0 and nodeid in rstatus:
            rstatus = rstatus[nodeid]['redis']
            for stat in rstatus:
                if stat['state'] != 'RUNNING':
                    msg='Redis on node with id %s with port %s is not running.' % (nodeid, stat['port'])
                    j.events.opserror( msg, category='monitoring')
