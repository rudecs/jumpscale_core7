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


class SocketServerClient():

    def __init__(self, addr="localhost", port=9999, key="1234"):
        self.port = port
        self.addr = addr
        self.key = key
        self.type = "client"
        self.timeout = 60
        self.initclient()
        self.dataleftover = ""

    def senddata(self, data):
        """
        sends data & wait for result
        """
        data = "A" + struct.pack("I", len(data)) + data
        try:
            self.socket.sendall(data)
        except Exception as e:
            print(("sendata error: %s" % e))
            self.reinitclient()
            return self.senddata(data)

    def reinitclient(self):
        try:
            self.socket.close()
        except Exception as e:
            print("Error in send to socket, could not close the socket")
            print(e)
        self.initclient()

    def initclient(self):
        self.dataleftover = ""
        for t in range(1000):
            if self._initclient() == True:
                self.socket.settimeout(self.timeout)
                return True
        raise RuntimeError("Connection timed out to server %s" % self.addr)

    def _initclient(self):
        print(("try to connect to %s:%s" % (self.addr, self.port)))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sender.settimeout(2)
        data = '**connect** whoami:%s key:%s' % (j.application.whoAmI, self.key)
        try:
            self.socket.connect((self.addr, self.port))
            self.senddata(data)
        except Exception as e:
            try:
                print(("connection error to %s %s" % (self.addr, self.port)))
            except:
                pass
            try:
                self.socket.close()
            except:
                pass
            print(("initclient error:%s, sleep 1 sec." % e))
            sleep(1)
            return False

        print("connected")
        if self.readdata() == "ok":
            return True
        else:
            return False

    def getsize(self, data):
        check = data[0]
        if check != "A":
            raise RuntimeError("error in tcp stream, first byte needs to be 'A'")
        sizebytes = data[1:5]
        size = struct.unpack("I", sizebytes)[0]
        return data[5:], size

    def _readdata(self, data):
        print("select")
        ready = select.select([self.socket], [], [], self.timeout)
        if ready[0]:
            data += self.socket.recv(4096)
        return data

    def readdata(self):
        """
        """
        data = self.dataleftover
        self.dataleftover = ""
        # wait for initial data packet
        while len(data) < 6:  # need 5 bytes at least
            data = self._readdata(data)

        data, size = self.getsize(data)  # 5 first bytes removed & size returned

        while len(data) < size:
            data = self._readdata(data)

        self.dataleftover = data[size:]
        return data[0:size]
