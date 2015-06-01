from JumpScale import j

descr = """list atyourservice services"""

category = "ays"
organization = "jumpscale"
author = "khamisr@codescalers.com"
version = "1.0"
roles = []


def action(domain="", name="", instance="", reload=False):
    import re
    import json

    def _getServices():
        services = rcl.hgetalldict("ays:services")
        if domain or name or instance:
            key = '%s_%s_%s' % (domain or '[a-zA-Z0-9]*', name or '[a-zA-Z0-9]*', instance or '[a-zA-Z0-9]*')
            regex = re.compile(key)
            matched = [m.string for service in services.keys()
                       for m in [regex.search(service)] if m]
            return [services[m] for m in matched]
        else:
            return services

    rcl = j.clients.redis.getByInstance("system")
    if rcl.exists("ays:services") and not reload:
        services = rcl.hgetalldict("ays:services")
        if services:
            return _getServices()

    services = j.atyourservice.findServices(domain, name, instance)

    fields = ("domain", "producers", "args", "name", "instance", "noremote", "templatepath", "categories",
              "cmd", "parent", "hrddata", "path", "servicetemplate")
    for service in services:
        tdict = dict()
        for field in fields:
            tdict[field] = getattr(service, field)
        tdict['priority'] = service.getPriority()
        tdict['processDicts'] = service.getProcessDicts()
        tdict['tcpPorts'] = service.getTCPPorts()
        tdict['parents'] = service.findParents()
        tdict['isInstalled'] = service.isInstalled()
        tdict['dependencies'] = [{'domain':dep.domain, 'name':dep.name, 'instance':dep.instance} for dep in service.getDependencies()]
        tdict['dependencyChain'] = [{'domain':dep.domain, 'name':dep.name, 'instance':dep.instance} for dep in service.getDependencyChain()]
        tdict['children'] = service.listChildren()
        tdict['logPath'] = service.getLogPath()
        tdict['isLatest'] = service.isLatest()
        tdict['hrd'] = str(service.hrd)
        rcl.hset("ays:services", "%(domain)s_%(name)s_%(instance)s" % tdict, json.dumps(tdict))
    return _getServices()
