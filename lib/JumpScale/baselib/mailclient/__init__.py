from JumpScale import j
from .emailclient import EmailClient

j.base.loader.makeAvailable(j, 'clients')
j.clients.email = EmailClient()

