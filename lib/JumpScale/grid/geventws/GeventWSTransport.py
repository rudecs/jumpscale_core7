from JumpScale import j
import JumpScale.grid.serverbase
from JumpScale.grid.serverbase.DaemonClient import Transport
from JumpScale.grid.serverbase.TCPHATransport import TCPHATransport
import requests


class GeventWSTransport(Transport):

    def __init__(self, addr="localhost", port=9999, timeout=None, endpoint='rpc/', poolsize=100):
        scheme = 'http' if port != 443 else 'https'
        self.url = "%s://%s:%s/%s" % (scheme, addr, port, endpoint)
        self._id = None
        self.timeout = timeout
        self._session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=poolsize, pool_maxsize=poolsize, max_retries=5, pool_block=True)
        self._session.mount('{}://'.format(scheme), adapter)
        self._addr = addr
        self._port = port

    def connect(self, sessionid=None):
        """
        everwrite this method in implementation to init your connection to server (the transport layer)
        """
        self._id = sessionid
        if j.system.net.tcpPortConnectionTest(self._addr, self._port) is False:
            j.errorconditionhandler.raiseOperationalCritical("could not connect to server %s on port %s, is it running?" % (
                self._addr, self._port), category="transport.ws.gevent.init")

    def close(self):
        """
        close the connection (reset all required)
        """
        pass

    def sendMsg(self, category, cmd, data, sendformat="", returnformat="", retry=True, timeout=None):
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
        start = j.base.time.getTimeEpoch()
        if timeout is None:
            timeout = self.timeout
        if retry:
            rcv = None
            while rcv is None:
                now = j.base.time.getTimeEpoch()
                if timeout and now > start + timeout:
                    break
                try:
                    rcv = self._session.post(self.url, data=data2, headers=headers, timeout=timeout)
                except Exception as e:
                    raise RuntimeError("error to send msg to %s,error was %s" % (self.url, e))

        else:
            print("NO RETRY ON REQUEST WS TRANSPORT")
            rcv = requests.post(self.url, data=data2, headers=headers, timeout=timeout)

        if rcv is None:
            eco = j.errorconditionhandler.getErrorConditionObject(msg='timeout on request to %s' % self.url, msgpub='',
                                                                  category='gevent.transport')
            return "4", "m", j.db.serializers.getMessagePack().dumps(eco.__dict__)

        if rcv.ok is False:
            eco = j.errorconditionhandler.getErrorConditionObject(msg='error 500 from webserver on %s' % self.url, msgpub='',
                                                                  category='gevent.transport')
            return "6", "m", j.db.serializers.getMessagePack().dumps(eco.__dict__)

        try:
            return j.servers.base._unserializeBinReturn(rcv.content)
        finally:
            rcv.close()


class GeventWSHATransport(TCPHATransport):

    def __init__(self, connections, timeout=None, poolsize=100):
        TCPHATransport.__init__(self, connections, GeventWSTransport, timeout, poolsize=poolsize)

    @property
    def ipaddr(self):
        return self._connection[0]
