from JumpScale import j

def cb():
    from .Cgroups import Cgroups
    return Cgroups()

j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform._register('cgroups', cb)

