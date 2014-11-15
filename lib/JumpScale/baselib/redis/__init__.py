from JumpScale import j

from .Redis import RedisFactory

j.base.loader.makeAvailable(j, 'clients')

j.clients.redis=RedisFactory()


