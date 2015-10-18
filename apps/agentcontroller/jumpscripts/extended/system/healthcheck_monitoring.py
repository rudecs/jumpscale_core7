from JumpScale import j

descr = """
Monitor system status
"""

organization = "jumpscale"
name = 'healthcheck_monitoring'
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

period = 600 #always in sec
enable = True
async = True
roles = ["master"]
log=False
queue = "hypervisor"

def action():
    import JumpScale.grid.gridhealthchecker
    import JumpScale.baselib.redis
    import time
    try:
        import ujson as json
    except:
        import json

    rediscl = j.clients.credis.getRedisClient('127.0.0.1', 9999)
    results, errors = j.core.grid.healthchecker.runOnAllNodesByCategory()
    rediscl.hset('healthcheck:monitoring', 'results', json.dumps(results))
    rediscl.hset('healthcheck:monitoring', 'errors', json.dumps(errors))
    rediscl.hset('healthcheck:monitoring', 'lastcheck', time.time())

    if errors:
        for nid, categories in errors.iteritems():
            for cat, data in categories.iteritems():
                msg='%s on node %s seems to be having issues' % (cat, nid)
                print msg
                # j.events.opserror(msg, 'monitoring')
