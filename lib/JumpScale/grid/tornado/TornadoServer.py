from JumpScale import j
import struct

import tornado.ioloop
import tornado.web
import JumpScale.grid.serverbase
import time


class MainHandlerRPC(tornado.web.RequestHandler):

    """
    processes the incoming web requests
    """

    def initialize(self, server):
        self.server = server

    def responseRaw(self,data,start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [data]

    def post(self, *args, **kwargs):
        data = self.request.body
        data = data.decode('utf-8')
        
        category, cmd, data2, informat, returnformat, sessionid = j.servers.base._unserializeBinSend(data)
        resultcode, returnformat, result = self.server.daemon.processRPCUnSerialized(cmd, informat, returnformat, data2, sessionid, category=category)
        data3 = j.servers.base._serializeBinReturn(resultcode, returnformat, result)
        # resultcode,returnformat,result2=j.servers.base._unserializeBinReturn(data3)
        # if result != result2:
        #     from IPython import embed
        #     print "DEBUG NOW serialization not work in post"
        #     embed()
        self.write(data3)
        # self.set_header('Content-Type','application/octet-stream')
        self.flush()


# class MainHandlerGetWork(tornado.web.RequestHandler):

#     """
#     processes the incoming web requests
#     """

#     def initialize(self, server):
#         self.server = server

#     @tornado.web.asynchronous
#     def get(self):
#         print 'Request via GET', self
#         from IPython import embed
#         print "DEBUG NOW get"
#         embed()

#     def wait(self, nrsec):
#         self.server.ioloop.add_timeout(self.server.ioloop.time() + 10, self.done)

#     def done(self):
#         self.write("YES WORKED")
#         self.finish()


class TornadoServer():

    def __init__(self, addr, port, sslorg=None, ssluser=None, sslkeyvaluestor=None):
        """
        @param handler is passed as a class
        """
        self.port = port
        self.addr = addr
        self.key = "1234"
        self.nr = 0
        # self.jobhandler = JobHandler()
        self.daemon = j.servers.base.getDaemon(sslorg=sslorg, ssluser=ssluser, sslkeyvaluestor=sslkeyvaluestor)
        self.application = tornado.web.Application([(r"(.*)", MainHandlerRPC, dict(server=self)), ])
        self.type = "tornado"

    def start(self):
        print(("started on %s" % self.port))
        self.application.listen(self.port)

        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.ioloop.start()

    def addCMDsInterface(self, MyCommands, category=""):
        self.daemon.addCMDsInterface(MyCommands, category)

    def _stack_context_handle_exception(self, *kwargs):
        print kwargs
        import ipdb; ipdb.set_trace()
