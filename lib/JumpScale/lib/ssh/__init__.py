
from JumpScale import j


def cb():
    from .disklayout import manager
    return manager.DiskManagerFactory()

j.base.loader.makeAvailable(j, 'ssh')
j.ssh._register('disklayout', cb)
