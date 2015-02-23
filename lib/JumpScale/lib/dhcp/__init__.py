from JumpScale import j

def cb():
    from .dhcp import DhcpFactory
    return DhcpFactory()

j.base.loader.makeAvailable(j, 'system.platform.dhcp')
j.system.platform._register('dhcp', cb)
