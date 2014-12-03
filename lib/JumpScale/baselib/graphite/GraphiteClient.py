
from JumpScale import j

import socket
import time
# import urllib.request, urllib.parse, urllib.error

try:
    import urllib
except:
    import urllib.parse as urllib


class GraphiteClient():
    def __init__(self):


        self._SERVER = '127.0.0.1'
        self._CARBON_PORT = 2003
        self._GRAPHITE_PORT = 8081
        self._url = "http://%s:%s/render" % (self._SERVER, self._GRAPHITE_PORT)

        
        # self.sock.connect((self.CARBON_SERVER, self.CARBON_PORT))


    def send(self,msg):
        """
        e.g. foo.bar.baz 20
        """
        out=""
        for line in msg.split("\n"):
            out+='%s %d\n'%(line,int(time.time()))
        sock = socket.socket()
        sock.connect((self._SERVER, self._CARBON_PORT))
        sock.sendall(out)
        sock.close()

    def close(self):
        pass

    def query(self, query_=None, **kwargs):
        import requests
        query = query_.copy() if query_ else dict()
        query.update(kwargs)
        query['format'] = 'json'
        if 'from_' in query:
            query['from'] = query.pop('from_')
        qs = urllib.urlencode(query)
        url = "%s?%s" % (self._url, qs)
        return requests.get(url).json()
