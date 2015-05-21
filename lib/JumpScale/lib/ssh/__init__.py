
from JumpScale import j


def disklayout():
    from .disklayout import manager
    return manager.DiskManagerFactory()


def openwrt():
    from .openwrt import manager
    return manager.OpenWRTFactory()

j.base.loader.makeAvailable(j, 'ssh')
j.ssh._register('disklayout', disklayout)
j.ssh._register('openwrt', openwrt)
