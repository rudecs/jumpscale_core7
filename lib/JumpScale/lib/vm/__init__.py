from JumpScale import j

def cb():
    from .vm import VirtualMachinesFactory
    return VirtualMachinesFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('vm', cb)
