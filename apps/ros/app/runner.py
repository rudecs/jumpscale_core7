from JumpScale import j
from JumpScale.baselib import cmdutils

import os
import sys
import swagger
from eve import Eve
from eve.utils import config
from eve.render import send_response
from eve_docs import eve_docs
from eve_docs.config import get_cfg
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL

from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple
from . import modelloader
from . import api
from .converters import osis2mongo
from .converters import osis2sqlalchemy
from .sqlalchemy import common
import urlparse
import importlib

import copy

STATIC_PATH = '/opt/jumpscale7/jslib/swagger/'

HOOKSMAP = {'on_insert_%s': 'pre_create',
            'on_inserted_%s': 'post_create',
            'on_fetched_%s': 'get',
            'on_replace_%s': 'pre_update',
            'on_replaced_%s': 'post_update',
            'on_update_%s': 'pre_partial_update',
            'on_updated_%s': 'post_partial_update',
            'on_delete_%s': 'pre_delete',
            'on_deleted_%s': 'post_delete',
            'on_fetched_item_%s': 'get',
            }

ID_FIELD = 'guid'
ITEM_LOOKUP_FIELD = ID_FIELD
config.ID_FIELD = ID_FIELD
config.ITEM_LOOKUP_FIELD = ID_FIELD

BASE_SETTINGS = {
        'DEBUG': True,
        'ID_FIELD': ID_FIELD,
        'IF_MATCH':False,
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

def hookevents(namespace, app):
    for model in app.settings['DOMAIN'].keys():
        modulename = 'models.hooks.%s.%s' % (namespace, model)
        try:
            module = importlib.import_module(modulename)
            for dbevent, hookmethod in HOOKSMAP.iteritems():
                evehook = dbevent % model 
                if hasattr(module, hookmethod):
                    hook = getattr(app, evehook)
                    hook += getattr(module, hookmethod)
        except ImportError:
            print 'Could not find module %s' % modulename
            pass # we dont require all hooks to exist

def prepare_mongoapp(namespace, models):
    dbname = namespace if namespace != 'system' else 'js_system'
    my_settings = BASE_MONGO_SETTINGS.copy()
    my_settings['MONGO_DBNAME'] = dbname
    my_settings['MONGO_QUERY_BLACKLIST'] = []
    my_settings['DOMAIN'] = osis2mongo.generateDomain(models)
    # init application
    app = Eve('osis', settings=my_settings, static_url_path=STATIC_PATH)
    swagger.expose_docs(app, STATIC_PATH)
    hookevents(namespace, app)
    return app

def prepare_sqlapp(namespace, models, sqluri):
    my_settings = BASE_SETTINGS.copy()
    parts = urlparse.urlparse(sqluri)
    if parts.scheme == 'sqlite':
        j.system.fs.createDir(parts.path)
        sqluri = j.system.fs.joinPaths(sqluri, '%s.sqlite' % namespace)
    my_settings['SQLALCHEMY_DATABASE_URI'] = sqluri
    my_settings['SQLALCHEMY_ECHO'] = True
    my_settings['IF_MATCH'] = False
    my_settings['SQLALCHEMY_RECORD_QUERIES'] = True
    my_settings['DOMAIN'] = osis2sqlalchemy.generateDomain(namespace, models)
    app = Eve(validator=ValidatorSQL, data=SQL, settings=my_settings, static_url_path=STATIC_PATH)
    db = app.data.driver
    common.Base.metadata.bind = db.engine
    db.Model = common.Base
    db.create_all()
    swagger.expose_docs(app, STATIC_PATH)
    hookevents(namespace, app)
    return app

def start(basedir, hrd):
    port = hrd.getInt('instance.param.port')
    mongdb_instance = hrd.get('instance.param.mongodb.connection', '')
    autoreload = True if hrd.get('instance.param.autoreload', '').lower() == "yes" else False
    sqluri = hrd.get('instance.param.sqlalchemy.uri', '')
    use_reloader = True if hrd.get('instance.param.eve.use_reloader', '').lower() == 'yes' else False
    use_debugger = True if hrd.get('instance.param.eve.use_debugger', '').lower() == 'yes' else False

    if mongdb_instance:
        mongohrd = j.application.getAppInstanceHRD('mongodb_client', mongdb_instance) 
        BASE_SETTINGS['MONGO_HOST'] = mongohrd.get('instance.param.addr')
        BASE_SETTINGS['MONGO_PORT'] = mongohrd.getInt('instance.param.port')

    apps = dict()
    fullspecs = modelloader.find_models(basedir)
    namespaces = []
    for type_, specs in fullspecs.iteritems():
        for namespace, models in specs.iteritems():
            if type_ == 'sql':
                app = prepare_sqlapp(namespace, models, sqluri)
            else:
                app = prepare_mongoapp(namespace, models)
            apps['/models/%s' % namespace] = app
            namespaces.append(namespace)

    if apps:
        apiapp = api.register_api(namespaces)
        apps['/api'] = apiapp
        application = DispatcherMiddleware(apiapp, apps)
        # let's roll
        run_simple('0.0.0.0', port, application, use_reloader=use_reloader, use_debugger=use_debugger)

