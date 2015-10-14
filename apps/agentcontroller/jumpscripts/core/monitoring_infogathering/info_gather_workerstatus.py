from JumpScale import j
import JumpScale.baselib.redis

descr = """
Monitor CPU and mem of worker
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

async = False
roles = []

period = 600

log = True


def action():
    rediscl = j.clients.redis.getByInstance('system')
    timemap = {'default': '-2m', 'io': '-2h', 'hypervisor': '-10m', 'process': '-1m'}
    results = list()

    for queue in ('io', 'hypervisor', 'default', 'process'):
        result = {'category': 'Workers'}
        lastactive = rediscl.hget('workers:heartbeat', queue) or 0
        timeout = timemap.get(queue)
        if j.base.time.getEpochAgo(timeout) < lastactive:
            result['state'] = 'OK'
        else:
            result['state'] = 'ERROR'

        lastactive = j.base.time.epoch2HRDateTime(lastactive) if lastactive else 'never'
        result['message'] = '*%s last active*: %s.' % (queue.upper(), lastactive)
        results.append(result)
    return results

if __name__ == "__main__":
    print action()
