from fabric.api import run

@task
def setupNetwork(ifaces):
    interfaces = ''
    for iface, config in ifaces.iteritems():
        interfaces += '''
auto %s
iface %s inet static
    address %s
    netmask %s
    gateway %s''' % (iface, iface, config[0], config[1], config[2])
    run("echo %s > /etc/network/interfaces" % interfaces)
    run("restart networking")