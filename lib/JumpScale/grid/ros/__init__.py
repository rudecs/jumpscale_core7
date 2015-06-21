from JumpScale import j

def cb():
    from JumpScale.grid.ros.factory import ClientFactory
    return ClientFactory()


j.base.loader.makeAvailable(j, 'clients')
j.clients._register('ros', cb)
