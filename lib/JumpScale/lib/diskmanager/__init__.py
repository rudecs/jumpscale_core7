from JumpScale import j

def cb():
    from .Diskmanager import Diskmanager
    return Diskmanager()

j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform._register('diskmanager', cb)

