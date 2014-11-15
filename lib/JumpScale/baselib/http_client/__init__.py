from JumpScale import j
from .HttpClient import HttpClient
j.base.loader.makeAvailable(j, 'clients')
j.clients.http = HttpClient()
