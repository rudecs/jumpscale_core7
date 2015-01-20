from JumpScale import j

descr = """executes a jpackage action_jpackage"""

name = "jpackage_action"
category = "jpackages"
organization = "jumpscale"
author = "rkhamis@incubaid.com"
version = "1.0"
gid, nid, _ = j.application.whoAmI
roles = []

def action(domain, pname, version, action):
    
    if version:
        package = j.packages.find(domain, pname, version)[0]
    else:
        package = j.packages.findNewest(domain, pname)

    message = "%s on %s successful" % (action, pname)

    if action == 'update':
        package.install()
    elif hasattr(package, action):
        getattr(package, action)()
    else:
        message = "%s on %s failed" % (action, pname)

    return message
