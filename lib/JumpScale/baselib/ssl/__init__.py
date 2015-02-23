from JumpScale import j

def cb():
    from .SSL import SSL
    return SSL()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('ssl', cb)
