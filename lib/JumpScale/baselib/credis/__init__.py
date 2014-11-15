from JumpScale import j

from .CRedis import CRedisFactory

j.base.loader.makeAvailable(j, 'clients')

j.clients.credis=CRedisFactory()


