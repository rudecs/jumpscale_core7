from JumpScale import j

def cb():
    from .TornadoFactory import TornadoFactory
    return TornadoFactory()

j.base.loader.makeAvailable(j, 'servers')
j.servers._register('tornado', cb)
