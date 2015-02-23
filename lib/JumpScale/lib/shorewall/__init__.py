from JumpScale import j

def cb():
    from .shorewall import ShorewallFactory
    return ShorewallFactory()

j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform._register('shorewall', cb)
