from JumpScale import j

def cb():
    from .CRedis import CRedisFactory
    return CRedisFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('credis', cb)


