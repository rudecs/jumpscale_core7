from JumpScale import j

def cb():
    from .Sandboxer import Sandboxer
    return Sandboxer()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('sandboxer', cb)

