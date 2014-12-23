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
    netmask %s''' % (iface, iface, config[0], config[1])
    sudo('echo "%s" > /etc/network/interfaces' % interfaces)
    sudo("ifdown -a; ifup -a")