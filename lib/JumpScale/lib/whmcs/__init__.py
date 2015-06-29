from JumpScale import j

def cb():
    from .WhmcsFactory import WhmcsFactory
    return WhmcsFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('whmcs', cb)

