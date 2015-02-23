from JumpScale import j

def cb():
    from .BlobStor import BlobStorFactory
    import JumpScale.baselib.hash
    return BlobStorFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('blobstor', cb)
