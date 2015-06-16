from JumpScale import j

import os
import importlib
import jinja2

from sqlalchemy.ext.hybrid import hybrid_property
from eve_sqlalchemy.decorators import registerSchema
from sqlalchemy.orm import column_property, relationship

tmplDir = j.system.fs.joinPaths(j.system.fs.getDirName(__file__),'templates')
jinjaEnv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(tmplDir),
        )

def generateDomain(namespace, spec):
    domain = dict()
    template = jinjaEnv.get_template('sqlalchemy.py')
    for modelname, modelspec in spec.iteritems():
        for propspec in modelspec.properties:
            ttype=propspec.type
            if ttype.startswith('list'):
                ttype = 'list'
            elif ttype.startswith('dict'):
                ttype = 'dict'
            propspec.ttype = ttype

    result = template.render(spec=spec)
    sqlalchemyfolder = j.system.fs.joinPaths(tmplDir, '..',  '..', '..', 'models', 'sqlalchemy')
    sqlalchemyfolder = os.path.abspath(sqlalchemyfolder)
    namespacefile = j.system.fs.joinPaths(sqlalchemyfolder, '%s.py' % namespace)
    j.system.fs.writeFile(namespacefile, result)
    module = importlib.import_module("models.sqlalchemy.%s" % namespace)
    for modelname, modelspec in spec.iteritems():
        modelclass = getattr(module, modelname)
        registerSchema(modelspec.name)(modelclass)
        domain[modelname] = modelclass._eve_schema[modelspec.name]
        domain[modelname].update({'item_url': 'regex("[a-f0-9\-]+")'})
    return domain

