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
from eve_sqlalchemy import SQL as _SQL
from eve_sqlalchemy.validation import ValidatorSQL
from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple
import flask.ext.sqlalchemy as flask_sqlalchemy
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

BASE_MONGO_SETTINGS = copy.deepcopy(BASE_SETTINGS)
BASE_MONGO_SETTINGS['MONGO_HOST'] = '127.0.0.1'
BASE_MONGO_SETTINGS['MONGO_PORT'] = 27017

def hookevents(namespace, app):
    # Get all events per namespace
    modulename = 'models.hooks.%s' % namespace
    namespace_hooks = {}
    try:
        module = importlib.import_module(modulename)
        for _, hookmethod in HOOKSMAP.iteritems():
            if hasattr(module, hookmethod):
                namespace_hooks[hookmethod] = getattr(module, hookmethod)
        print 'Finished loading gloabl namespace hookd for namespace %s' % namespace
    except ImportError:
        pass
    
    for model in app.settings['DOMAIN'].keys():
        modulename = 'models.hooks.%s.%s' % (namespace, model)
        module = None
        
        try:
            module = importlib.import_module(modulename)
        except ImportError:
            pass

        for dbevent, hookmethod in HOOKSMAP.iteritems():
            evehook = dbevent % model
            hook = getattr(app, evehook)
            if hookmethod in namespace_hooks:
                hook += namespace_hooks[hookmethod]
            if module and hasattr(module, hookmethod):
                hook += getattr(module, hookmethod)
        print 'Finished Loading hooks for module %s' % modulename
        

def prepare_mongoapp(namespace, models):
    dbname = namespace if namespace != 'system' else 'js_system'
    my_settings = copy.deepcopy(BASE_MONGO_SETTINGS)
    my_settings['MONGO_DBNAME'] = dbname
    my_settings['MONGO_QUERY_BLACKLIST'] = []
    my_settings['DOMAIN'] = osis2mongo.generateDomain(namespace, models)
    # init application
    app = Eve('osis', settings=my_settings, static_url_path=STATIC_PATH)
    swagger.expose_docs(app, STATIC_PATH)
    hookevents(namespace, app)
    return app

def prepare_sqlapp(namespace, models, sqluri, from_spec_file=True):
    my_settings = copy.deepcopy(BASE_SETTINGS)
    parts = urlparse.urlparse(sqluri)
    if parts.scheme == 'sqlite':
        j.system.fs.createDir(parts.path)
        sqluri = j.system.fs.joinPaths(sqluri, '%s.sqlite' % namespace)
    my_settings['SQLALCHEMY_DATABASE_URI'] = sqluri
    my_settings['SQLALCHEMY_ECHO'] = True
    my_settings['IF_MATCH'] = False
    my_settings['SQLALCHEMY_RECORD_QUERIES'] = True

    if from_spec_file:
        my_settings['DOMAIN'] = osis2sqlalchemy.generateDomainFromSpecFile(namespace, models)
    else:
        my_settings['DOMAIN'] = osis2sqlalchemy.generateDomainFromModelFiles(namespace, models)
        
    db = flask_sqlalchemy.SQLAlchemy()

    class SQL(_SQL):
        driver = db
       
        def init_app(self, app):
            try:
                # FIXME: dumb double initialisation of the
                # driver because Eve sets it to None in __init__
                self.driver = db
                self.driver.app = app
                self.driver.init_app(app)
            except Exception as e:
                raise ConnectionException(e)

            self.register_schema(app)
       
    app = Eve(validator=ValidatorSQL, data=SQL, settings=my_settings, static_url_path=STATIC_PATH)
    db = app.data.driver
    common.Base.metadata.bind = db.engine
    db.Model = common.Base
    db.create_all()
    swagger.expose_docs(app, STATIC_PATH)
    hookevents(namespace, app)
    return app

def start(basedir, hrd):
    port = hrd.getInt('instance.param.osis2.port')
    mongdb_instance = hrd.get('instance.param.osis2.mongodb.connection', '')
    sqluri = hrd.get('instance.param.osis2.sqlalchemy.uri', '')
    use_reloader = hrd.getBool('instance.param.osis2.use_reloader')
    use_debugger = hrd.getBool('instance.param.osis2.use_debugger')

    if mongdb_instance:
        mongohrd = j.application.getAppInstanceHRD('mongodb_client', mongdb_instance) 
        BASE_SETTINGS['MONGO_HOST'] = mongohrd.get('instance.param.addr')
        BASE_SETTINGS['MONGO_PORT'] = mongohrd.getInt('instance.param.port')

    apps = dict()
    
    fullspecs = modelloader.find_model_specs(basedir)
    namespaces = []
    for type_, specs in fullspecs.iteritems():
        for namespace, models in specs.iteritems():
            if type_ == 'sql':
                app = prepare_sqlapp(namespace, models, sqluri)
            else:
                app = prepare_mongoapp(namespace, models)
            apps['/models/%s' % namespace] = app
            namespaces.append(namespace)

    # Auto load sqlalchemy models from python files
    spaces_models = modelloader.find_model_files(basedir)
    for namespace, models in spaces_models.iteritems():
        app = prepare_sqlapp(namespace, models, sqluri, False)
        apps['/models/%s' % namespace] = app
        namespaces.append(namespace)

    if apps:
        apiapp = api.register_api(namespaces)
        apps['/api'] = apiapp
        application = DispatcherMiddleware(apiapp, apps)
        # let's roll
        run_simple('0.0.0.0', port, application, use_reloader=use_reloader, use_debugger=use_debugger)

