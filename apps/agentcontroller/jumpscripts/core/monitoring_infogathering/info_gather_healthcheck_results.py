from JumpScale import j
import time
import JumpScale.baselib.redis

descr = """
Gather node's healthchecks (used in macro in portal)
"""

organization = "jumpscale"
name = 'info_gather_healthcheck_results'
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "gather.healthchecker"

period = 0 #always in sec
enable = True
async = False
roles = []

log=False

def action():
    result = dict()
    def get(check):
        if redisclient.hexists("healthcheck:status",  check):
            status = j.basetype.boolean.fromString(redisclient.hget("healthcheck:status", check)) #should return True or false
            lastcheck = redisclient.hget("healthcheck:lastcheck", check) #should return time
            return status, lastcheck


    redisclient = j.clients.redis.getByInstance('system')
    redisport = j.clients.redis.getPort('system')
    result['disks'] = get('disks')
    check = 'redis:%s' % redisport
    result[check] = get(check)
        
    for worker in ['worker_hypervisor_0', 'worker_default_0', 'worker_default_1', 'worker_io_0']:
        check = 'workers:%s' % worker
        result[check] = get(check)

    return result

if __name__ == "__main__":
    print action()