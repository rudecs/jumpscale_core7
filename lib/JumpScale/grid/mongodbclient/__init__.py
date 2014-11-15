from JumpScale import j


from .MongoDBClient import MongoDBClient

j.base.loader.makeAvailable(j, 'clients')
j.clients.mongodb = MongoDBClient()


