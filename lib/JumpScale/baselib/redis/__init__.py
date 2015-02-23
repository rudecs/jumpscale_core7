from JumpScale import j

def cb():
    from .Redis import RedisFactory
    return RedisFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('redis', cb)
