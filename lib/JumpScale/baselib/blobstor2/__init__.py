from JumpScale import j

from .BlobStorFactory import *
import JumpScale.baselib.hash

j.base.loader.makeAvailable(j, 'clients')
j.base.loader.makeAvailable(j, 'servers')

j.clients.blobstor2=BlobStorFactory()
j.servers.blobstor2=BlobStorFactoryServer()
