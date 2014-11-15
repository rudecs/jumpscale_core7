from JumpScale import j
from .TipcFactory import TipcFactory

j.base.loader.makeAvailable(j, 'servers')
j.servers.tipc = TipcFactory()
