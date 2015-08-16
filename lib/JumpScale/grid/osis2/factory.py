from JumpScale import j
from .client import Client

class ClientFactory(object):
    def get(self, instance='main', ip='', user='', passwd=''):
        hrd = j.application.getAppInstanceHRD(name="osis2_client",instance=instance)
        host = hrd.get('instance.param.osis2.client.addr')
        port = str(hrd.get('instance.param.osis2.client.port'))
        url = "http://%s:%s" % (host, port)
        return Client(url)