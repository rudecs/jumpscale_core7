
from JumpScale import j

descr = """
remotly install a cpunode
"""

organization = "jumpscale"
name = "cpunode_install"
author = "christophe@incubaid.com"
license = "bsd"
version = "1.0"
async = True
roles = []
log = True


def action(node, parent):
    parent = j.atyourservice.getFromStr(parent)
    node = j.atyourservice.getFromStr(node, parent)
    reversePort = node.hrd.get('instance.ssh.port')

    if not j.system.net.waitConnectionTest("localhost", reversePort, 60):
        return False

    node.install(deps=True, reinstall=True)
    return True

if __name__ == "__main__":
    action("jumpscale:node.ssh:cpu1","jumpscale:location:dev")