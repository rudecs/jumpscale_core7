from JumpScale import j
from GitFactory import GitFactory

j.base.loader.makeAvailable(j, 'clients')
j.clients.git = GitFactory()

