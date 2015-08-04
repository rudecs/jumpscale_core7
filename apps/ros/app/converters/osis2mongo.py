from JumpScale import j
import re

typemap = {'str': 'string',
           'int': 'integer',
           'float': 'float',
           'dict(str)': 'dict',
           'dict': 'dict',
           'list(str)': 'list',
           'list': 'list',
           'list(int)': 'list',
           'bool': 'boolean',
           'datetime':'datetime',
           'objectid':'objectid'}

def generateDomain(namespace, spec):
    domain = dict()
    for modelname, modelspec in spec.iteritems():
        domain[modelname] = generateModel(namespace, modelspec)
    return domain


def getType(namespace, type):
    """
    Check if field type defines nested schema
    If so, returns it otherwise return None
    """
    # check if list(Model) or just Model
    info = re.search('((?P<type>\w+)\()?(?P<model>\w+)\)?', type).groupdict()
    childspec = j.core.specparser.getChildModelSpec('osismodel', namespace, info['model'], die=False)
    if not childspec:
        return None, None
    else:
        return childspec, (info['type'] or 'dict' )

def generateModel(namespace, modelspec):
    schema = dict()
    model = {'item_url': 'regex(".*")',
            'item_lookup_field': 'guid',
            'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE'],
            'resource_methods': ['GET', 'POST', 'DELETE'],
            'url': modelspec.name,
            'schema': schema}
    
    # Add expires index if TTL in tags
    if modelspec.tags and 'TTL' in modelspec.tags:
        splitted = modelspec.tags.split(':')
        if len(splitted) == 2:
            try:
                ttl = int(splitted[-1])
                model['mongo_indexes'] = {'TTL' : [('lastupdatedat', 1), ('expireAfterSeconds', ttl)]}
            except ValueError:
                pass

    prop = {'type': 'string', 'default':'', 'required': False, 'nullable': True}
    schema['guid'] = prop
    
    for propspec in modelspec.properties:
        prop = {'nullable': True}
        schema[propspec.name] = prop
        ttype=propspec.type
        default=propspec.default
        args=""
        if default==None:
            prop['default'] = ""
            prop['required'] = True
        else:
            prop['default'] = default
            prop['required'] = False
        
        schematype, t = getType(namespace, ttype)
        if ttype.startswith('list'):
            ttype = 'list'
        elif ttype.startswith('dict'):
            ttype = 'dict'
        if schematype:
            """
            root@js:~# curl -d '{"value": {"id":3, "value":2}}' -H 'Content-Type: application/json' http://172.17.0.8:5545/models/system/hamdies
            """
            ttype = t
            subschema = generateModel(namespace, schematype)['schema']
            if t == 'dict':
                prop['schema'] = subschema
            elif t == 'list':
                prop['schema'] = {'type': 'dict', 'schema' : subschema}
        prop['type'] = typemap[ttype]

    return model
