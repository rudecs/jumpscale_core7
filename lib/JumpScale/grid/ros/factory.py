from JumpScale import j
from .client import Client

class ClientFactory(object):
    def get(self, instance='main', ip='', user='', passwd=''):
        hrd = j.application.getAppInstanceHRD(name="ros_client",instance=instance)
        host = hrd.get('instance.param.ros.client.addr')
        port = str(hrd.get('instance.param.ros.client.port'))
        url = "http://%s:%s" % (host, port)
        return Client(url)