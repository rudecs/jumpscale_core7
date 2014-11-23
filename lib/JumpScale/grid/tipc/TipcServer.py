from JumpScale import j

import tornado.ioloop
import tornado.web
import JumpScale.grid.serverbase
import time
import socket



class TipcServer(object):

    def __init__(self, servaddr, sslorg=None, ssluser=None, sslkeyvaluestor=None):
        """
        @param handler is passed as a class
        """
        self.srvaddr = servaddr
        self.daemon = j.servers.base.getDaemon(sslorg=sslorg, ssluser=ssluser, sslkeyvaluestor=sslkeyvaluestor)

    def start(self):
  
        self.socket = socket.socket(family=socket.AF_TIPC, type=socket.SOCK_RDM)
        self.socket.bind(self.srvaddr)
        print(('server started, addr:', self.socket.getsockname()))
        while True:
            data, addr = self.socket.recvfrom(66000)
            returndata = self.handleData(data, addr)
            self.socket.sendto(returndata, addr)

    def handleData(self, data, addr):
        category, cmd, cmddata, informat, returnformat, sessionid = j.servers.base._unserializeBinSend(data)
        resultcode, returnformat, result = self.daemon.processRPCUnSerialized(cmd, informat, returnformat, cmddata, \
            sessionid, category=category)
        return j.servers.base._serializeBinReturn(resultcode, returnformat, result)

    def addCMDsInterface(self, MyCommands, category=""):
        self.daemon.addCMDsInterface(MyCommands, category)
