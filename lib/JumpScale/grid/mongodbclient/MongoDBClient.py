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
        # jp=j.packages.findNewest(name="mongodb_client",domain='jumpscale')
        # jp=jp.load(instancename)
        # hrd = jp.hrd_instance
        hrd = j.application.getAppInstanceHRD(name="mongodb_client",instance=instancename)
        # hrd = j.core.hrd.get('/opt/jumpscale7/hrd/jumpscale/mongodb_client/%s/hrd' % instancename)
        if hrd is None:
            j.events.opserror_critical("Could not find mongodb_client for instance %s" % instancename)
        ipaddr = hrd.get("param.addr")
        port = hrd.getInt("param.port")    
        ssl = False
        if j.application.config.exists('ssl'):
            ssl = j.application.config.getBool('ssl')
        replicaset = ""
        if j.application.config.exists('replicaset'):
            replicaset = j.application.config.get('replicaset')
        if replicaset == "":
            return MongoClient(host=ipaddr, port=port, ssl=ssl)
        else:
            return MongoReplicaSetClient(host=ipaddr, port=port, ssl=ssl, replicaSet=replicaset)
