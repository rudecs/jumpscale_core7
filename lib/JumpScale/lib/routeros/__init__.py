from JumpScale import j

def cb():
    from .RouterOS import RouterOSFactory
    return RouterOSFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('routeros', cb)
