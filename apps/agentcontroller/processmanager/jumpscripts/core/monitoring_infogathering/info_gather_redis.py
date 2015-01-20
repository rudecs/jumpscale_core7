from JumpScale import j

descr = """
Checks Redis server status
"""

organization = "jumpscale"
name = 'info_gather_redis'
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "system.redisstatus"

async = False
roles = []

period=0

log=False

def action():
    import JumpScale.baselib.redis
    ports = []
    redisdefs = j.tools.startupmanager.getProcessDefs('redis')
    for redisdef in redisdefs:
        for redisport in redisdef.ports:
            if redisport and j.basetype.integer.checkString(redisport):
                ports.append(int(redisport))

    result = dict()
    for port in ports:
        pids = j.system.process.getPidsByPort(port)
        if not pids:
            result[port] = {'state': 'HALTED', 'memory_usage': 0, 'memory_max': 0}
        else:
            rcl = j.clients.redis.getRedisClient('127.0.0.1', port)
            state = 'RUNNING' if rcl.ping() else 'BROKEN'
            maxmemory = float(rcl.config_get('maxmemory').get('maxmemory', 0))
            used_memory = rcl.info()['used_memory']
            if (used_memory / maxmemory) * 100 > 90:
                state = 'WARNING'
            result[port] = {'state': state, 'memory_usage': used_memory, 'memory_max': maxmemory}

    return result
