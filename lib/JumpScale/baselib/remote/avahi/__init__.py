from JumpScale import j

def cb():
    from .Avahi import Avahi
    return Avahi()

j.base.loader.makeAvailable(j, 'remote')
j.remote._register('avahi', cb)
