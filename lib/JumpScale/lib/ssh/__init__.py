
from JumpScale import j


def disklayout():
    from .disklayout import manager
    return manager.DiskManagerFactory()


def openwrt():
    from .openwrt import manager
    return manager.OpenWRTFactory()


def nginx():
    from .nginx import manager
    return manager.NginxManagerFactory()


j.base.loader.makeAvailable(j, 'ssh')

j.ssh._register('disklayout', disklayout)
j.ssh._register('openwrt', openwrt)
j.ssh._register('nginx', nginx)
