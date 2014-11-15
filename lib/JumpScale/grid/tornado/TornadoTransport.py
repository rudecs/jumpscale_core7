from JumpScale import j

import JumpScale.grid.serverbase
from JumpScale.grid.serverbase.DaemonClient import Transport


import requests

class TornadoTransport(Transport):
    def __init__(self, addr="localhost", port=9999):

        self.timeout = 60
        self.url = "http://%s:%s/rpc/" % (addr, port)
        self._id = None

    def connect(self, sessionid=None):
        """
        everwrite this method in implementation to init your connection to server (the transport layer)
        """
        self._id = sessionid

    def close(self):
        """
        close the connection (reset all required)
        """
        pass

    def sendMsg(self, category, cmd, data, sendformat="", returnformat=""):
        """
        overwrite this class in implementation to send & retrieve info from the server (implement the transport layer)

        @return (resultcode,returnformat,result)
                item 0=cmd, item 1=returnformat (str), item 2=args (dict)
        resultcode
            0=ok
            1= not authenticated
            2= method not found
            2+ any other error
        """

        headers = {'content-type': 'application/raw'}
        data2 = j.servers.base._serializeBinSend(category, cmd, data, sendformat, returnformat, self._id)
        r = requests.post(self.url, data=data2, headers=headers)
        if r.ok==False:
            eco=j.errorconditionhandler.getErrorConditionObject(msg='error 500 from webserver', msgpub='', \
                category='tornado.transport')
            return 99,"m",j.db.serializers.msgpack.dumps(eco.__dict__)

        return j.servers.base._unserializeBinReturn(r.content)
