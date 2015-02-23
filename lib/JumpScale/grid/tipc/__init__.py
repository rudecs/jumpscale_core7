from JumpScale import j

def cb():
    from .TipcFactory import TipcFactory
    return TipcFactory()

j.base.loader.makeAvailable(j, 'servers')
j.servers._register('tipc', cb)
