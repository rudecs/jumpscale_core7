from JumpScale import j

def cb():
    from .ServerBaseFactory import ServerBaseFactory
    return ServerBaseFactory()

j.base.loader.makeAvailable(j, 'servers')
j.servers._register('base', cb)
