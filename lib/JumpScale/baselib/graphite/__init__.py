from JumpScale import j
from .GraphiteClient import GraphiteClient
j.base.loader.makeAvailable(j, 'clients')
j.clients.graphite = GraphiteClient()


