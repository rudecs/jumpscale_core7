from JumpScale import j

from .BlobStor import BlobStorFactory
import JumpScale.baselib.hash

j.base.loader.makeAvailable(j, 'clients')

j.clients.blobstor=BlobStorFactory()
