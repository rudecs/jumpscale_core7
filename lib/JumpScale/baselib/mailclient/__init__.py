from JumpScale import j

def cb():
    from .emailclient import EmailClient
    return EmailClient()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('email', cb)

