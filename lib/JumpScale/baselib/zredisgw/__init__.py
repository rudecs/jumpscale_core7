from JumpScale import j

from .ZRedisGWFactory import *
import JumpScale.baselib.hash

j.base.loader.makeAvailable(j, 'clients')
# j.base.loader.makeAvailable(j, 'servers')

j.clients.zredisgw=ZRedisGWFactory()

