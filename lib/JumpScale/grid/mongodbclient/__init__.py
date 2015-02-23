from JumpScale import j

def cb():
    from .MongoDBClient import MongoDBClient
    return MongoDBClient()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('mongodb', cb)


