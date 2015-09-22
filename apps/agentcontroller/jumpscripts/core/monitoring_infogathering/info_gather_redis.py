from JumpScale import j

descr = """
Checks Redis server status
"""

organization = "jumpscale"
name = 'info_gather_redis'
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

async = False
roles = []

period=0

log=False

def action():
    import JumpScale.baselib.redis
    ports = {}
    errors = list()
    results = list()
    
    for instance in j.atyourservice.findServices(name='redis'):
        
        if not instance.isInstalled():
            continue
        
        for redisport in instance.getTCPPorts():
            if redisport:
                ports[instance.instance] = ports.get(instance.instance, [])
                ports[instance.instance].append(int(redisport))
    result = dict()
    for instance, ports_val in ports.iteritems():
        for port in ports_val:
            pids = j.system.process.getPidsByPort(port)
            if not pids:
                errors.append({'port': port, 'state': 'HALTED', 'memory_usage': 0, 'memory_max': 0})
            else:
                rcl = j.clients.redis.getByInstance(instance)
                state = 'RUNNING' if rcl.ping() else 'BROKEN'
                maxmemory = float(rcl.config_get('maxmemory').get('maxmemory', 0))
                used_memory = rcl.info()['used_memory']
                if (used_memory / maxmemory) * 100 > 90:
                    state = 'WARNING'
                result = {'port': port, 'state': state, 'memory_usage': used_memory, 'memory_max': maxmemory}

                if rcl.ping():
                    results.append(result)
                else:
                    errors.append(result)

    return {'results': results, 'errors': errors}

if __name__ == "__main__":
    print action()

