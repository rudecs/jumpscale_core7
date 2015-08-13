from JumpScale import j

def cb():
    from .openvcloud import OpenvcloudFactory
    return OpenvcloudFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('openvcloud', cb)
