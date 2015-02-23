from JumpScale import j

def cb():
    from .CiscoSwitchManager import CiscoSwitchManager
    return CiscoSwitchManager()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('ciscoswitch', cb)
