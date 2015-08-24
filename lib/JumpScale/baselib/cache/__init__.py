from JumpScale import j

def cb():
    from .Cache import *
    return CacheFactory()

j.base.loader.makeAvailable(j, 'db')
j.db._register('cache', cb)
