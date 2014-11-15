from JumpScale import j

from .Webdis import WebdisFactory

j.base.loader.makeAvailable(j, 'clients')

j.clients.webdis=WebdisFactory()


