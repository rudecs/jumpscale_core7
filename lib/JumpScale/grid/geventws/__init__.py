from JumpScale import j

def cb():
    from .GeventWSFactory import GeventWSFactory
    return GeventWSFactory()

j.base.loader.makeAvailable(j, 'servers')
j.servers._register('geventws', cb)
