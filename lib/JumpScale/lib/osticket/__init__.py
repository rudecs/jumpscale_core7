from JumpScale import j

def cb():
    from .OSTicketFactory import OSTicketFactory
    return OSTicketFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('osticket', cb)
