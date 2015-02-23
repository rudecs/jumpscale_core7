from JumpScale import j

def cb():
    from .RemoteSystem import RemoteSystem
    return RemoteSystem()

j.base.loader.makeAvailable(j, 'remote')
j.remote._register('system', cb)
