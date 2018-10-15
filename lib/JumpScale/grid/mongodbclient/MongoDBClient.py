from JumpScale import j

from pymongo import MongoClient, MongoReplicaSetClient

class MongoDBClient:

    def get(self, host='localhost', port=27017):
        try:
            client = MongoClient(host, int(port))
        except Exception as e:
            raise RuntimeError('Could not connect to mongodb server on %s:%s\nerror:%s' % (host, port,e))
        else:
            return client

    def getByInstance(self, instancename):
        config = j.core.config.get("mongodb_client", instancename)
        if config is None:
            j.events.opserror_critical("Could not find mongodb_client for instance %s" % instancename)
        ipaddr = config.get("addr")
        port = config.get("port")
        ssl = config.get("ssl", False)
        replicaset = config.get("replicaset")
        if replicaset:
            return MongoReplicaSetClient(ipaddr, port=port, ssl=ssl, replicaSet=replicaset)
        else:
            return MongoClient(host=ipaddr, port=port, ssl=ssl)
            
