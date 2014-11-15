from JumpScale import j
from elasticsearch import Elasticsearch


class ElasticsearchFactory:

    def get(self, ip="localhost", port=9200, timeout=60):
        j.logger.log("check elastic search reachable on %s on port %s" % (ip, port), level=4, category='osis.init')
        port=int(port)
        res = j.system.net.waitConnectionTest(ip, int(port), timeout)
        if res == False:
            raise RuntimeError("Could not find a running elastic server instance on %s:%s" % (ip, port))
        client = Elasticsearch('http://%s:%s/' % (ip, port))
        status = j.system.net.checkListenPort(port)
        if not status:
            raise RuntimeError("Could find port of elastic server instance on %s:%s, but status was not ok." % (ip, port))
        j.logger.log("OK elastic search is reachable on %s on port %s" % (ip, port), level=4, category='osis.init')
        return client
