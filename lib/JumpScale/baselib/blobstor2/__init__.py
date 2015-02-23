from JumpScale import j

def cbc():
    from .BlobStorFactory import BlobStorFactory
    return BlobStorFactory()

def cbs():
    from .BlobStorFactory import BlobStorFactoryServer
    return BlobStorFactoryServer()


j.base.loader.makeAvailable(j, 'clients')
j.base.loader.makeAvailable(j, 'servers')

j.clients._register('blobstor2', cbc)
j.servers._register('blobstor2', cbs)
