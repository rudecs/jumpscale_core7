
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


def action(node, parent, masterAddr):
    print "###########################"
    print "# cpu node installation #"
    print "###########################"

    try:
        parent = j.atyourservice.getFromStr(parent)
        node = j.atyourservice.getFromStr(node, parent)
        reversePort = node.hrd.get('instance.ssh.port')

        print "cpunode install : wait for ssh connection"
        if not j.system.net.waitConnectionTest("localhost", reversePort, 10):
            # timeout of the connection
            j.atyourservice.remove(node.domain, node.name, node.instance, node.parent)
            j.events.opserror_critical('connection to the node timeout, abord installation')

        print "cpunode install : start jumpscale installation"
        node.install(deps=True, reinstall=True)

        data = {
            'instance.remote.port': reversePort,
            'instance.remote.address': masterAddr,
            'instance.remote.login': 'root',
            'instance.local.port': 22,
            'instance.local.address': 'localhost'
        }
        autossh = j.atyourservice.new(name='autossh', instance=node.instance, parent=node, args=data)
        autossh.consume('node', node.instance)
        print "cpunode install: install autossh service"
        count = 0
        while count < 3:
            try:
                print "############# Try install autossh ##############"
                autossh.install(deps=True)
                break
            except:
                count += 1

    except:
        j.atyourservice.remove(node.domain, node.name, node.instance, node.parent)
        j.events.opserror_critical('Unexpected error, abord installation')

    return True

if __name__ == "__main__":
    action("jumpscale:node.ssh:cpu1", "jumpscale:location:openvc_nodes", '172.17.42.100')