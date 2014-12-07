from JumpScale import j

from .Daemon import Daemon
import time
import struct
import ujson as json
import codecs

class ServerBaseFactory():

    def getDaemon(self, name="unknown", sslorg=None, ssluser=None, sslkeyvaluestor=None):
        """

        is the basis for every daemon we create which can be exposed over e.g. zmq or sockets or http


        daemon=j.servers.base.getDaemon()

        class MyCommands():
            def __init__(self,daemon):
                self.daemon=daemon

            #session always needs to be there
                    def pingcmd(self,session=session):
                        return "pong"

                    def echo(self,msg="",session=session):
                        return msg

        daemon.addCMDsInterface(MyCommands,category="optional")  #pass as class not as object !!! chose category if only 1 then can leave ""

        #now you need to pass this to a protocol server, its not usable by itself

        """

        zd = Daemon(name=name)
        if ssluser:
            from JumpScale.baselib.ssl.SSL import SSL
            zd.ssluser = ssluser
            zd.sslorg = sslorg
            zd.keystor = SSL().getSSLHandler(sslkeyvaluestor)
            try:
                zd.keystor.getPrivKey(sslorg, ssluser)
            except:
                zd.keystor.createKeyPair(sslorg, ssluser)
        else:
            zd.keystor = None
            zd.ssluser = None
            zd.sslorg = None
        return zd

    def initSSL4Server(self, organization, serveruser, sslkeyvaluestor=None):
        from JumpScale.baselib.ssl.SSL import SSL
        ks = SSL().getSSLHandler(sslkeyvaluestor)
        ks.createKeyPair(organization, serveruser)

    def getDaemonClientClass(self):
        """
        example usage, see example for server at self.getDaemon (implement transport still)

        DaemonClientClass=j.servers.base.getDaemonClientClass()

        myClient(DaemonClientClass):
            def __init__(self,ipaddr="127.0.0.1",port=5651,org="myorg",user="root",passwd="1234",ssl=False,roles=[]):
                self.init(org=org,user=user,passwd=passwd,ssl=ssl,roles=roles)

            def _connect(self):
                #everwrite this method in implementation to init your connection to server (the transport layer)
                pass

            def _close(self):
                #close the connection (reset all required)
                pass


            def _sendMsg(self, cmd,data,sendformat="m",returnformat="m"):
                #overwrite this class in implementation to send & retrieve info from the server (implement the transport layer)
                #@return (resultcode,returnformat,result)
                #item 0=cmd, item 1=returnformat (str), item 2=args (dict)
                #resultcode
                #    0=ok
                #    1= not authenticated
                #    2= method not found
                #    2+ any other error
                pass
                #send message, retry if needed, retrieve message

        client=myClient()
        print client.echo("atest")

        """
        from .DaemonClient import DaemonClient
        return DaemonClient

    def _serializeBinSend(self, category, cmd, data, sendformat, returnformat, sessionid):
        lencategory = len(category)
        lencmd = len(cmd)
        lendata = len(data)
        lenreturnformat = len(returnformat)
        lensendformat = len(sendformat)
        lensessionid = len(sessionid)
        # packed = struct.pack("<IIIIII", lencategory, lencmd, lendata, lensendformat, lenreturnformat, lensessionid).decode('utf-32')
        packed = '%s:%s:%s:%s:%s:%s:' % (lencategory, lencmd, lendata, lensendformat, lenreturnformat, lensessionid)
        return packed + category + cmd + data + sendformat + returnformat + sessionid

    def _unserializeBinSend(self, data):
        """
        return cmd,data,sendformat,returnformat,sessionid
        """
        # fformat = "<IIIIII"
        # size = struct.calcsize(fformat)
        # datasizes = struct.unpack(fformat, bytearray(data[0:size], 'utf-32'))
        data = data.split(':', 6)
        lengths, data = data[:-1], data[-1]
        lengths = [int(length) for length in lengths]
        for length in lengths:
            res = data[0:length]
            data = data[length:]
            yield res

    def _serializeBinReturn(self, resultcode, returnformat, result):
        lendata = len(result)
        if resultcode == None:
            resultcode = '\x00'
        lenreturnformat = len(returnformat)
        # packed = struct.pack("<II", lenreturnformat, lendata)
        packed = ':%s:%s:' % (lenreturnformat, lendata)
        return resultcode + packed + returnformat + result

    def _unserializeBinReturn(self, data):
        """
        return resultcode,returnformat,result
        """
        resultcode, lenreturnformat, lendata, restofdata = data.split(':', 3)
        return (resultcode, restofdata[:int(lenreturnformat)], restofdata[int(lenreturnformat):])
