from JumpScale import j

def cb():
    from .LRUCacheFactory import LRUCacheFactory
    return LRUCacheFactory()

j.base.loader.makeAvailable(j, 'db')
j.db._register('cachelru', cb)


