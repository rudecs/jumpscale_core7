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

async = True
roles = []

period = 600

log = True

def action():
    import JumpScale.baselib.redis
    ports = {}
    results = list()

    for instance in j.atyourservice.findServices(name='redis'):
        
        if not instance.isInstalled():
            continue
        
        for redisport in instance.getTCPPorts():
            if redisport:
                ports[instance.instance] = ports.get(instance.instance, [])
                ports[instance.instance].append(int(redisport))

    for instance, ports_val in ports.iteritems():
        for port in ports_val:
            result = {'category': 'Redis'}
            pids = j.system.process.getPidsByPort(port)
            if not pids:
                state = 'ERROR'
                used_memory = 0
                maxmemory = 0
            else:
                rcl = j.clients.redis.getByInstance(instance)
                state = 'OK' if rcl.ping() else 'ERROR'
                maxmemory = float(rcl.config_get('maxmemory').get('maxmemory', 0))
                used_memory = rcl.info()['used_memory']
                if (used_memory / maxmemory) * 100 > 90:
                    state = 'WARNING'

            size, unit = j.tools.units.bytes.converToBestUnit(used_memory)
            msize, munit = j.tools.units.bytes.converToBestUnit(maxmemory)
            used_memory = '%.2f %sB' % (size, unit)
            maxmemory = '%.2f %sB' % (msize, munit)
            result['message'] = '*Port*: %s. *Memory usage*: %s/ %s' % (port, used_memory, maxmemory)
            result['state'] = state
            results.append(result)
            print results

    return results

if __name__ == "__main__":
    print action()

