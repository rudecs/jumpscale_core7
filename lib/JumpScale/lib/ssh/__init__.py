
from JumpScale import j


def ubuntu():
    from .ubuntu import manager
    return manager.UbuntuManagerFactory()


def disklayout():
    from .disklayout import manager
    return manager.DiskManagerFactory()


def openwrt():
    from .openwrt import manager
    return manager.OpenWRTFactory()


def nginx():
    from .nginx import manager
    return manager.NginxManagerFactory()


def ufw():
    from .ufw import manager
    return manager.UFWManagerFactory()


def server():
    from .server import manager
    return manager.SSHFactory()


def nfs():
    from .nfs import manager
    return manager.NFSFactory()


def aoe():
    from .aoe import manager
    return manager.AOEFactory()


def connect(addr='localhost', port=22, passwd=None):
    j.ssh.connection = j.remote.cuisine.connect(addr, port=22, passwd=passwd)
    return j.ssh.connection

j.base.loader.makeAvailable(j, 'ssh')

j.ssh.connect = connect

j.ssh._register('disklayout', disklayout)
j.ssh._register('openwrt', openwrt)
j.ssh._register('nginx', nginx)
j.ssh._register('ufw', ufw)
j.ssh._register('ubuntu', ubuntu)
j.ssh._register('server', server)
j.ssh._register('nfs', nfs)
j.ssh._register('aoe', aoe)
