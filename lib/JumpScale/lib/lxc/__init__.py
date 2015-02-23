from JumpScale import j

def cb():
    from .Lxc import Lxc
    return Lxc()

j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform._register('lxc', cb)

