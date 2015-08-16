from JumpScale import j
import jinja2

from flask import Flask
import json
import os
from flask.ext.bootstrap import Bootstrap
from flask import send_from_directory

tmplDir = j.system.fs.joinPaths(j.system.fs.getDirName(__file__), 'templates')
jinjaEnv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(tmplDir),
        )

STATIC_PATH = '/opt/jumpscale7/jslib/swagger/'

def register_api(namespaces):
    app = Flask('API')
    app.debug = True
    Bootstrap(app)
    
    @app.route('/namespace', methods=['GET'])
    def list_namespaces():
        print namespaces
        return json.dumps(namespaces)
    
    @app.route('/', methods=['GET'])
    def home():
        template = jinjaEnv.get_template('home.html')
        return template.render(namespaces=namespaces)
        
    @app.route('/lib/<path:path>')
    def js(path):
        return send_from_directory(os.path.join(STATIC_PATH, 'lib'), path)
    
    @app.route('/css/<path:path>')
    def css(path):
        return send_from_directory(os.path.join(STATIC_PATH, 'css'), path)
    
    @app.route('/images/<path:path>')
    def images(path):
        return send_from_directory(os.path.join(STATIC_PATH, 'images'), path)
    
    @app.route('/fonts/<path:path>')
    def fonts(path):
        return send_from_directory(os.path.join(STATIC_PATH, 'fonts'), path)
    
    return app

