from JumpScale import j

import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer

# gevent.monkey.patch_all()

from flask import Flask, request, Response, render_template

app = Flask(__name__)
app.debug = True

class PMWSServer():
    def __init__(self):        
        self.http_server = WSGIServer(('127.0.0.1', 8001), app)
    
    def start(self):
        self.http_server.serve_forever()

    @classmethod
    def event_stream(self):
        count = 0
        while True:
            gevent.sleep(1)
            yield 'data: %s\n\n' % count
            count += 1

    @app.route('/my_event_source')
    def sse_request():
        return Response(PMWSServer.event_stream(),mimetype='text/event-stream')

    @app.route('/')
    def page():
        return render_template('sse.html')

# s=PMWSServer()
# s.start()

