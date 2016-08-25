from JumpScale import j

def cb():
    from .JS8Stub import JS8Stub
    return JS8Stub()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('js8stub', cb)
