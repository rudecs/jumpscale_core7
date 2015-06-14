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
        hrd = j.application.getAppInstanceHRD(name="mongodb_client",instance=instancename)
        if hrd is None:
            j.events.opserror_critical("Could not find mongodb_client for instance %s" % instancename)
        ipaddr = hrd.get("instance.param.addr")
        port = hrd.getInt("instance.param.port")    
        ssl = False
        if hrd.exists('instance.param.ssl'):
            ssl = hrd.getBool('instance.param.ssl')
        replicaset = ""
        if hrd.exists('instance.param.replicaset'):
            replicaset = hrd.get('instance.param.replicaset')
        if replicaset == "":
            return MongoClient(host=ipaddr, port=port, ssl=ssl)
        else:
            return MongoReplicaSetClient(ipaddr, port=port, ssl=ssl, replicaSet=replicaset)
