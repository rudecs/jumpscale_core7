from JumpScale import j

from pymongo import MongoClient, MongoReplicaSetClient

class MongoDBClient:

    def get(self, host='localhost', port=27017):
        try:
            client = MongoClient(host, int(port))
        except Exception,e:
            raise RuntimeError('Could not connect to mongodb server on %s:%s\nerror:%s' % (host, port,e))
        else:
            return client

    def getByInstance(self, instancename):
        jp=j.packages.findNewest(name="mongodb_client",domain='jumpscale')
        jp=jp.load(instancename)
        hrd = jp.hrd_instance
        if hrd is None:
            j.events.opserror_critical("Could not find mongodb_client for instance %s" % instancename)
        ipaddr = hrd.get("mongodb.client.addr")
        port = hrd.getInt("mongodb.client.port")    
        ssl = False
        if j.application.config.exists('mongodb.client.ssl'):
            ssl = j.application.config.getBool('mongodb.client.ssl')
        replicaset = ""
        if j.application.config.exists('mongodb.client.replicaset'):
            replicaset = j.application.config.get('mongodb.client.replicaset')
        if replicaset == "":
            return MongoClient(host=ipaddr, port=port, ssl=ssl)
        else:
            return MongoReplicaSetClient(host=ipaddr, port=port, ssl=ssl, replicaSet=replicaset)
