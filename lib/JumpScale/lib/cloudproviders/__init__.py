from JumpScale import j

def cb():
    from .factory import Factory
    return Factory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('cloudproviders', cb)

