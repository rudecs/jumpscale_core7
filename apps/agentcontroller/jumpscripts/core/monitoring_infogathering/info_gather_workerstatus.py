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
category = "monitor.healthcheck"

async = False
roles = []

log=False

def action():
    rediscl = j.clients.redis.getByInstance('system')
    timemap = {'default': '-2m', 'io': '-2h', 'hypervisor': '-10m','process':'-1m'}
    result = {'results':[], 'errors': []}
    for queue in ('io', 'hypervisor', 'default', 'process'):
        lastactive = rediscl.hget('workers:heartbeat', queue) or 0
        timeout = timemap.get(queue)
        stats = {'lastactive': lastactive, 'queue':queue}
        if j.base.time.getEpochAgo(timeout) < lastactive:
            stats['state'] = 'RUNNING'
            result['results'].append(stats)
        else:
            stats['state'] = 'HALTED'
            result['errors'].append(stats)
    return result

if __name__ == "__main__":
    print action()