from JumpScale import j


class TipcFactory(object):

    def getServer(self, servaddr, sslorg=None, ssluser=None, sslkeyvaluestor=None):
        """
        HOW TO USE:
        daemon=j.servers.tornado.getServer(port=4444)

        class MyCommands():
            def __init__(self,daemon):
                self.daemon=daemon

            #session always needs to be there
            def pingcmd(self,session=session):
                return "pong"

            def echo(self,msg="",session=session):
                return msg

        daemon.addCMDsInterface(MyCommands,category="optional")  #pass as class not as object !!! chose category if only 1 then can leave ""

        daemon.start()

        """
        from .TipcServer import TipcServer
        return TipcServer(servaddr, ssluser=ssluser, sslorg=sslorg, sslkeyvaluestor=sslkeyvaluestor)

    def getClient(self, servaddr, category="core", org="myorg", user="root", passwd="passwd", ssl=False, roles=[]):
        from .TipcTransport import TipcTransport
        from JumpScale.grid.serverbase.DaemonClient import DaemonClient
        trans = TipcTransport(servaddr)
        cl = DaemonClient(org=org, user=user, passwd=passwd, ssl=ssl, transport=trans)
        return cl.getCmdClient(category)
