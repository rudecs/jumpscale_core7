from JumpScale import j

def cb():
    from .client import AYSPMClientFactory
    return AYSPMClientFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('ayspm', cb)
