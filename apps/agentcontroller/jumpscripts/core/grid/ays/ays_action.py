from JumpScale import j

descr = """executes an atyourservice action"""

name = "ays_action"
category = "ays"
organization = "jumpscale"
author = "rkhamis@incubaid.com"
version = "1.0"
gid, nid, _ = j.application.whoAmI
roles = []

def action(domain, sname, instance, action):

    services = j.atyourservice.findServices(domain, sname, instance)

    if services:
        service = services[0]
    else:
        return "%s on %s failed" % (action, sname)

    message = "%s on %s successful" % (action, sname)

    if action == 'update':
        service.install()
    elif hasattr(service, action):
        getattr(service, action)()
    else:
        message = "%s on %s failed" % (action, sname)
    return message
