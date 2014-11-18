from JumpScale import j
import struct
import socketserver
import socket
try:
    import gevent

    def sleep(sec):
        gevent.sleep(sec)
except:
    import time

    def sleep(sec):
        time.sleep(sec)

import select

from .QSocketServerClient import *


class QSocketServerHandler(socketserver.BaseRequestHandler):

    # def __init__(self):
    # SocketServer.BaseRequestHandler.__init__(self)
    #     SocketBase.__init__(self)

    def getsize(self, data):
        check = data[0]
        if check != "A":
            raise RuntimeError("error in tcp stream, first byte needs to be 'A'")
        sizebytes = data[1:5]
        size = struct.unpack("I", sizebytes)[0]
        return data[5:], size

    def _readdata(self, data):
        print("select")
        try:
            ready = select.select([self.socket], [], [], self.timeout)
            self.selectcounter += 1
            if self.selectcounter > 100:
                raise RuntimeError("recverror")

        except Exception as e:
            print(e)
            raise RuntimeError("recverror")

        if ready[0]:
            try:
                data += self.socket.recv(4096)
            except Exception as e:
                print(e)
                raise RuntimeError("recverror")
        else:
            print("timeout on select")
        return data

    def readdata(self):
        """
        """
        data = self.dataleftoever
        self.dataleftoever = ""
        # wait for initial data packet
        while len(data) < 6:  # need 5 bytes at least
            data = self._readdata(data)

        data, size = self.getsize(data)  # 5 first bytes removed & size returned

        while len(data) < size:
            data = self._readdata(data)

        self.dataleftover = data[size:]
        self.selectcounter = 0
        return data[0:size]

    def senddata(self, data):
        # message=j.core.messagehandler.data2Message(20,data)
        # for i in range(1000):
        # res=self._send(message)
        data = "A" + struct.pack("I", len(data)) + data
        self.socket.sendall(data)

    def handle(self):
        self.timeout = 60
        self.type = "server"
        self.dataleftoever = ""
        self.socket = self.request
        self.selectcounter = 0
        while True:
            try:
                data = self.readdata()
            except Exception as e:
                if str(e) == 'recverror':
                    self.socket.close()
                    return
                else:
                    raise RuntimeError("Cannot read data from client, unknown error: %s" % e)

            if data.find("**connect**") != -1:
                try:
                    self.senddata("ok")
                    # print data
                    print("new client connected: %s,%s" % self.client_address)

                except Exception as e:
                    print("send error during connect:%s, will close socket" % e)
                    self.socket.close()
                    return
            else:
                result = j.system.socketserver._handledata(data)
                if result != None:
                    try:
                        self.senddata(result)
                    except Exception as e:
                        print("send error:%s, will close socket" % e)
                        self.socket.close()
                        return


class QSocketServer():

    def __init__(self, addr, port, key, datahandler):
        """
        @param datahandler is method with as argument(data) which is bytstr, what you want to send back should be returned out of method
        """
        self.port = port
        self.addr = addr
        self.key = key
        j.system.socketserver.key = key
        self.type = "server"
        j.system.socketserver._handledata = datahandler
        self.server = socketserver.TCPServer((self.addr, self.port), QSocketServerHandler)

    def start(self):
        print("started on %s" % self.port)
        self.server.serve_forever()


class QSocketServerFactory():

    def get(self, port, key, datahandler):
        return QSocketServer('', port, key, datahandler)

    def getClient(self, addr, port, key):
        return SocketServerClient(addr, port, key)

    def _handledata(self, data):
        print("default data handler for socketserver, please overrule, method is handledata")
        print("data received")
        print(data)
