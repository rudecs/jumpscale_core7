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
roles = ['master']
log=False
queue = "hypervisor"

def action(nid=None):
    import JumpScale.grid.gridhealthchecker
    import JumpScale.baselib.redis
    import time
    try:
        import ujson as json
    except:
        import json

    rediscl = j.clients.credis.getByInstance('system')
    if nid is None:
        results, errors = j.core.grid.healthchecker.runAll()
        rediscl.hset('healthcheck:monitoring', 'results', json.dumps(results))
        rediscl.hset('healthcheck:monitoring', 'errors', json.dumps(errors))
        rediscl.hset('healthcheck:monitoring', 'lastcheck', time.time())
    else:
        results, errors = j.core.grid.healthchecker.runAllOnNode(nid)
        rresults = json.loads(rediscl.hget('healthcheck:monitoring', 'results'))
        rerrors = json.loads(rediscl.hget('healthcheck:monitoring', 'errors'))
        rresults.pop(str(nid), None)
        rerrors.pop(str(nid), None)
        rresults.update(results)
        rerrors.update(errors)
        rediscl.hset('healthcheck:monitoring', 'errors', json.dumps(rerrors))
        rediscl.hset('healthcheck:monitoring', 'results', json.dumps(rresults))

    msg = "Issues in healtcheck:\n"
    if errors:
        for nid, categories in errors.iteritems():
            for cat, data in categories.iteritems():
                msg +='%s on node %s seems to be having issues\n' % (cat, nid)
                # j.events.opserror(msg, 'monitoring')
        print msg
        j.events.opserror_warning(msg, 'monitoring')

if __name__ == '__main__':
    action()

