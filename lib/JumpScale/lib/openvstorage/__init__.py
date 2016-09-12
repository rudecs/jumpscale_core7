from JumpScale import j

def cb():
    from .openvstorage import OpenvStorageFactory
    return OpenvStorageFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('openvstorage', cb)
