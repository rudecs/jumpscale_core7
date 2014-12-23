from fabric.api import task, sudo

@task
def setupNetwork(ifaces):
    interfaces = '''auto lo
iface lo inet loopback
'''
    for iface, config in ifaces.iteritems():
        interfaces += '''
auto %s
iface %s inet static
    address %s
    netmask %s
    gateway %s''' % (iface, iface, config[0], config[1], config[2])
    sudo('echo "%s" > /etc/network/interfaces' % interfaces)
    sudo("ifdown -a")
    sudo("ifup -a")