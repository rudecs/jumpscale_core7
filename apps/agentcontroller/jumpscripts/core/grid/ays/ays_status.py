from JumpScale import j

descr = """list atyourservice services"""

category = "ays"
organization = "jumpscale"
author = "khamisr@codescalers.com"
version = "1.0"
roles = []


def action(reload=False):
    import json

    rcl = j.clients.redis.getByInstance("system")

    services = j.atyourservice.findServices()

    for service in services:
        if not service.isInstalled():
            continue
        tdict = dict()
        tdict['ports'] = ', '.join( str(x) for x in service.getTCPPorts())
        tdict['domain'] = service.domain
        tdict['name'] = service.name
        tdict['instance'] = service.instance
        tdict['priority'] = service.getPriority()
        isrunning = service.actions.check_up_local(service,wait=False)
        tdict['status'] = 'RUNNING' if isrunning else 'HALTED'

        rcl.hset("ays:services:status", "%(domain)s_%(name)s_%(instance)s" % tdict, json.dumps(tdict))