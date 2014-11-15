from JumpScale import j

import JumpScale.grid.serverbase
from JumpScale.grid.serverbase.DaemonClient import Transport
import socket


class TipcTransport(Transport):
    def __init__(self, servaddr):
        self.servaddr = servaddr
        self._id = None
        self.sock = None

    def connect(self, sessionid=None):
        """
        everwrite this method in implementation to init your connection to server (the transport layer)
        """
        self._id = sessionid
        self.sock = socket.socket(family=socket.AF_TIPC, type=socket.SOCK_RDM)
        self.sock.setsockopt(socket.SOL_TIPC, socket.TIPC_SRC_DROPPABLE, 0)
        self.sock.setsockopt(socket.SOL_TIPC, socket.TIPC_IMPORTANCE, socket.TIPC_CRITICAL_IMPORTANCE)
        self.sock.setblocking(True)

    def close(self):
        """
        close the connection (reset all required)
        """
        self.sock.close()

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

        bindata = j.servers.base._serializeBinSend(category, cmd, data, sendformat, returnformat, self._id)
        self.sock.sendto(bindata, self.servaddr)
        outdata, addr = self.sock.recvfrom(66000)
        return j.servers.base._unserializeBinReturn(outdata)
