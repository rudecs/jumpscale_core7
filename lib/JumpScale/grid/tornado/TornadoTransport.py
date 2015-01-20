from JumpScale import j

import JumpScale.grid.serverbase
from JumpScale.grid.serverbase.DaemonClient import Transport
from JumpScale.grid.serverbase.TCPHATransport import TCPHATransport
import time


import requests

class TornadoTransport(Transport):
    def __init__(self, addr="127.0.0.1", port=9999, timeout=60):

        self.timeout = timeout
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

    def sendMsg(self, category, cmd, data, sendformat="", returnformat="", retry=True, timeout=60):
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
        headers = {'content-type': 'application/text'}
        data2 = j.servers.base._serializeBinSend(category, cmd, data, sendformat, returnformat, self._id)
        start=j.base.time.getTimeEpoch()
        if self.timeout:
            timeout = self.timeout
        if retry:
            rcv=None
            while rcv==None:
                now=j.base.time.getTimeEpoch()
                if now>start+timeout:
                    break
                try:
                    rcv = requests.post(url=self.url, data=data2, headers=headers, timeout=timeout)
                except Exception as e:
                    if str(e).find("Connection refused")!=-1:
                        print(("retry connection to %s"%self.url))
                        time.sleep(0.1)
                    else:
                        raise RuntimeError("error to send msg to %s,error was %s"%(self.url,e))

        else:
            print("NO RETRY ON REQUEST TORNADO TRANSPORT")
            rcv = requests.post(self.url, data=data2, headers=headers,timeout=timeout)

        if rcv==None:
            eco=j.errorconditionhandler.getErrorConditionObject(msg='timeout on request to %s'%self.url, msgpub='', \
                category='tornado.transport')
            s = j.db.serializers.get('j')
            return "4","j",s.dumps(eco.__dict__)
                    
        if rcv.ok==False:
            eco=j.errorconditionhandler.getErrorConditionObject(msg='error 500 from webserver on %s'%self.url, msgpub='', \
                category='tornado.transport')
            s = j.db.serializers.get('j')
            return "6","j",s.dumps(eco.__dict__)

        content = rcv.content.decode('utf-8')
        return j.servers.base._unserializeBinReturn(content)


class TornadoHATransport(TCPHATransport):
    def __init__(self, connections, timeout=None):
        TCPHATransport.__init__(self, connections, TornadoTransport, timeout)

    @property
    def ipaddr(self):
        return self._connection[0]
