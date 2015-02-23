from JumpScale import j

def cb():
    from .Webdis import WebdisFactory
    return WebdisFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('webdis', cb)


