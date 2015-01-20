from JumpScale import j
import JumpScale.baselib.redis

descr = """
Monitor CPU and mem of worker
"""

organization = "jumpscale"
name = 'workerstatus'
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "system.workerstatus"

async = False
roles = []

log=False

def action():
    rediscl = j.clients.redis.getByInstanceName('system', gevent=True)
    timemap = {'default': '-2m', 'io': '-2h', 'hypervisor': '-10m','process':'-1m'}
    result = dict()
    for queue in ('io', 'hypervisor', 'default', 'process'):
        lastactive = rediscl.hget('workers:heartbeat', queue) or 0
        timeout = timemap.get(queue)
        stats = {'lastactive': lastactive}
        if j.base.time.getEpochAgo(timeout) < lastactive:
            stats['state'] = 'RUNNING'
        else:
            stats['state'] = 'HALTED'
        result[queue] = stats
    return result
