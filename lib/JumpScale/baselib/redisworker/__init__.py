from JumpScale import j

from .RedisWorker import RedisWorkerFactory

j.base.loader.makeAvailable(j, 'clients')

j.clients.redisworker=RedisWorkerFactory()


