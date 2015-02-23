from JumpScale import j

def cb():
    from .RedisWorker import RedisWorkerFactory
    return RedisWorkerFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('redisworker', cb)


