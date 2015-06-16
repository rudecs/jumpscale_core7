from JumpScale import j
from JumpScale.baselib import cmdutils

import os
import sys

from eve import Eve
from eve.utils import config
from eve.render import send_response
from eve_docs import eve_docs
from eve_docs.config import get_cfg

from flask.ext.bootstrap import Bootstrap

from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL

from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple

from . import modelloader
from . import api
from .converters import osis2mongo
from .converters import osis2sqlalchemy
from .sqlalchemy import common

import copy



ID_FIELD = 'guid'
ITEM_LOOKUP_FIELD = ID_FIELD
config.ID_FIELD = ID_FIELD
config.ITEM_LOOKUP_FIELD = ID_FIELD

BASE_SETTINGS = {
        'DEBUG': True,
        'ID_FIELD': ID_FIELD,
        'ITEM_URL': 'regex("[a-f0-9\-]+")',
        'ITEM_LOOKUP_FIELD': ITEM_LOOKUP_FIELD,
        'RESOURCE_METHODS': ['GET', 'POST'],
        'ITEM_METHODS': ['GET', 'PATCH', 'PUT', 'DELETE'],
        'X_DOMAINS': '*',
        'X_HEADERS': ["X-HTTP-Method-Override", 'If-Match'],
        'PAGINATION_LIMIT': 100000
}

BASE_MONGO_SETTINGS = BASE_SETTINGS.copy()
BASE_MONGO_SETTINGS['MONGO_HOST'] = '127.0.0.1'
BASE_MONGO_SETTINGS['MONGO_PORT'] = 27017

def expose_docs(app):
    Bootstrap(app)
    @app.route('/docs/spec.json')
    def specs():
        cfg = copy.deepcopy(get_cfg())
        for model in cfg['domains'].values():
            for path in model.values():
                for method in path.values():
                    for param in method['params']:
                        if 'default' in param and callable(param['default']):
                            param['default'] = None
        return send_response(None, [cfg])
    app.register_blueprint(eve_docs, url_prefix='/docs')

def prepare_mongoapp(namespace, models):
    dbname = namespace if namespace != 'system' else 'js_system'
    my_settings = BASE_MONGO_SETTINGS.copy()
    my_settings['MONGO_DBNAME'] = dbname
    my_settings['MONGO_QUERY_BLACKLIST'] = []
    my_settings['DOMAIN'] = osis2mongo.generateDomain(models)
    # init application
    app = Eve('osis', settings=my_settings)
    expose_docs(app)
    return app

def prepare_sqlapp(namespace, models):
    my_settings = BASE_SETTINGS.copy()
    dbdir = j.system.fs.joinPaths(j.dirs.varDir, 'osis', )
    j.system.fs.createDir(dbdir)
    db = j.system.fs.joinPaths(dbdir, '%s.sqlite' % namespace)
    my_settings['SQLALCHEMY_DATABASE_URI'] = "sqlite:///%s" %db
    my_settings['SQLALCHEMY_ECHO'] = True
    my_settings['IF_MATCH'] = False
    my_settings['SQLALCHEMY_RECORD_QUERIES'] = True
    my_settings['DOMAIN'] = osis2sqlalchemy.generateDomain(namespace, models)
    app = Eve(validator=ValidatorSQL, data=SQL, settings=my_settings)
    db = app.data.driver
    common.Base.metadata.bind = db.engine
    db.Model = common.Base
    db.create_all()
    expose_docs(app)
    return app

def start(basedir, port):
    apps = dict()
    fullspecs = modelloader.find_models(basedir)
    namespaces = []
    for type_, specs in fullspecs.iteritems():
        for namespace, models in specs.iteritems():
            if type_ == 'sql':
                app = prepare_sqlapp(namespace, models)
            else:
                app = prepare_mongoapp(namespace, models)
            apps['/models/%s' % namespace] = app
            namespaces.append(namespace)

    if apps:
        apiapp = api.register_api(namespaces)
        apps['/api'] = apiapp
        application = DispatcherMiddleware(apiapp, apps)
        # let's roll
        run_simple('0.0.0.0', port, application, use_reloader=True, use_debugger=True)

