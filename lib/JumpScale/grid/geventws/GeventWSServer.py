from gevent import monkey
# monkey.patch_all(aggressive=False)
monkey.patch_socket()
monkey.patch_thread()
monkey.patch_time()
monkey.patch_ssl()
from JumpScale import j
from gevent.pywsgi import WSGIServer
from JumpScale.grid.serverbase import returnCodes
import time
import json
import gevent

MAXSIZE = 10 * 1024 ** 2 # 10MiB

def jsonrpc(func):

    def wrapper(s, environ, start_response):

        payload = json.loads(environ['wsgi.input'].read())

        try:
            method_name = payload['method']
            method_kwargs = payload.get('params', dict())
            return_code, return_format, data = func(s, method_name, **method_kwargs)
            if return_code == returnCodes.OK:
                result = {'result': data, 'id': payload['id'], 'jsonrpc': '2.0'}
            else:
                result = {'result': None, 'id': payload['id'], 'jsonrpc': '2.0', 'error': {'code': 1, 'data': data}}
        except Exception, e:
            result = s.invalidRequest()

        statuscode = '200 OK' if not result.get('error', None) else '500 Internal Server Error'

        start_response(
            status=statuscode,
            headers=[('Content-type', 'application/json-rpc')],  # headers must be a mutable list
        )

        return [json.dumps(result)]

    return wrapper

class GeventWSServer():

    def __init__(self, addr, port, sslorg=None, ssluser=None, sslkeyvaluestor=None, verbose=False):
        """
        @param handler is passed as a class
        """        
        self.port = port
        self.addr = addr
        self.key = "1234"
        self.nr = 0
        self.verbose = verbose
        # self.jobhandler = JobHandler()
        self.daemon = j.servers.base.getDaemon(sslorg=sslorg, ssluser=ssluser, sslkeyvaluestor=sslkeyvaluestor)
        self.server = WSGIServer(('', self.port), self.rpcRequest)
        
        self.type = "geventws"

        self.greenlets = {}
        self.now = 0
        self.fiveMinuteId=0
        self.hourId=0
        self.dayId=0

    def startClock(self,obj=None):

        self.schedule("timer", self._timer)
        self.schedule("timer2", self._timer2)

        if obj!=None:
            obj.now=self.now
            obj.fiveMinuteId=self.fiveMinuteId
            obj.hourId=self.hourId
            obj.dayId=self.dayId


    def _timer(self):
        """
        will remember time every 1 sec
        """
        # lfmid = 0

        while True:
            self.now = time.time()
            print("timer")
            gevent.sleep(1)

    def _timer2(self):
        """
        will remember time every 1 sec
        """
        # lfmid = 0

        while True:
            self.fiveMinuteId=j.base.time.get5MinuteId(self.now )
            self.hourId=j.base.time.getHourId(self.now )
            self.dayId=j.base.time.getDayId(self.now )
            print("timer2")
            gevent.sleep(200)            

    def schedule(self, name, ffunction, *args, **kwargs):
        self.greenlets[name] = gevent.greenlet.Greenlet(ffunction, *args, **kwargs)
        self.greenlets[name].start()
        return self.greenlets[name]


    def responseRaw(self,data,start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [data]
    
    def responseNotFound(self,start_response):
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return ['<h1>Not Found</h1>']

    def rpcRequest(self, environ, start_response):
        payloadsize = int(environ.get('CONTENT_LENGTH', 0))
        if environ["PATH_INFO"].strip("/") == "ping":
            return self.responseRaw("pong", start_response)
        if environ['REQUEST_METHOD'] == 'POST':
            if environ["CONTENT_TYPE"]=='application/raw':
                if payloadsize > MAXSIZE:
                    eco = j.errorconditionhandler.getErrorConditionObject(msg="Payload size too big")
                    resultdata = j.servers.base._serializeBinReturn(returnCodes.ERROR, "m", self.daemon.errorconditionserializer.dumps(eco.__dict__))
                    print(eco)
                    return self.responseRaw(resultdata, start_response)
                data=environ["wsgi.input"].read()
                category, cmd, data2, informat, returnformat, sessionid = j.servers.base._unserializeBinSend(data)
                if self.verbose:
                    print(category, cmd, data2)
                resultcode, returnformat, result = self.daemon.processRPCUnSerialized(cmd, informat, returnformat, data2, sessionid, category=category)
                data3 = j.servers.base._serializeBinReturn(resultcode, returnformat, result)
                return self.responseRaw(data3,start_response)
            elif environ['CONTENT_TYPE'].startswith('application/json'):
                if payloadsize > MAXSIZE:
                    return self.invalidRequest("Payload size too big")
                return self.handleJSONRPC(environ, start_response)
        return self.responseNotFound(start_response)

    def invalidRequest(self, msg="Invalid Request"):
        msg = {'error': {'code': -32600, 'message': msg}, 'id': None, 'jsonrpc': '2.0'}
        return msg

    @jsonrpc
    def handleJSONRPC(self, method, **params):
        category, cmd = method.split('.', 1)
        sessionid = params.pop('sessionid', None)
        session = self.daemon.getSession(sessionid=sessionid, cmd=cmd)
        return self.daemon.processRPC(cmd, params, 'j', session, category=category)

    # def router(self, environ, start_response):
    #     path = environ["PATH_INFO"].lstrip("/")
    #     if path == "" or path.rstrip("/") == "wiki":
    #         path == "wiki/system"
    #     print "path:%s" % path

    #     if path.find("favicon.ico") != -1:
    #         return self.processor_page(environ, start_response, self.filesroot, "favicon.ico", prefix="")

    #     ctx = RequestContext(application="", actor="", method="", env=environ,
    #                          start_response=start_response, path=path, params=None)
    #     ctx.params = self._getParamsFromEnv(environ, ctx)

    def start(self):
        print(("started on %s" % self.port))
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print "bye"

    def addCMDsInterface(self, MyCommands, category="",proxy=False):
        self.daemon.addCMDsInterface(MyCommands, category,proxy=proxy)
