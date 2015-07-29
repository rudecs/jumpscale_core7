import requests
import urllib
import os
import json

class RemoteError(Exception):
    def __init__(self, msg, statuscode=None):
        super(RemoteError, self).__init__(self, msg)
        self.statuscode = statuscode

class NotFound(RemoteError):
    pass

def extract_pk(data):
    link = data['self']['href']
    return link.split('/')[-1]

class ModelObject(object):
    def _dump(self):
        result = dict()
        for slot in self.__slots__:
            result[slot] = getattr(self, slot)
        return result

    def _update_pk(self, data):
        self._pk = extract_pk(data)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def __getitem__(self, name):
        return getattr(self, name)

    def __repr__(self):
        return "<%s id %s>" % (self.__class__.__name__, self._pk)

def Struct(*args, **kwargs):
    def init(self, *iargs, **ikwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
        for i in range(len(iargs)):
            setattr(self, args[i], iargs[i])
        for k,v in ikwargs.items():
            setattr(self, k, v)
        if '_links' in ikwargs:
            self._update_pk(ikwargs['_links'])

    name = kwargs.pop("_name", "MyStruct")
    kwargs.update(dict((k, None) for k in args if not '.' in k))
    return type(name, (ModelObject,), {'__init__': init, '__slots__': kwargs.keys()})

class Client(object):
    def __init__(self, baseurl):
        self._baseurl = baseurl
        for namespace in self._list_namespaces():
            url = os.path.join(self._baseurl, 'models', namespace.lstrip('/'))
            setattr(self, namespace, NameSpaceClient(url))

    def _list_namespaces(self):
        listurl = os.path.join(self._baseurl, 'api', 'namespace')
        return requests.get(listurl).json()
    
    def _list_categories_for_namespace(self, namespace):
        if namespace in self._list_namespaces():
            url = os.path.join(self._baseurl, 'models', namespace.lstrip('/'))
            return NameSpaceClient(url)._list_categories()
        
    def _get_status(self, session=None):
        return "RUNNING"
    
    def _import_from_Path(self, namespace, category):
        raise NotImplemented()
    
    def _create_name_space_category(self, namespace, category, path):
        raise NotImplemented()
    
    def _export(self, namespace, categoryname, outputpath, session=None):
        # https://github.com/Jumpscale/jumpscale_core7/blob/master/lib/JumpScale/grid/osis/OSISCMDS.py
        raise NotImplemented()
     
class NameSpaceClient(object):
    def __init__(self, baseurl):
        self._baseurl = baseurl
        self._load_namespace()

    def _load_namespace(self):
        specurl = os.path.join(self._baseurl, 'docs', 'spec.json')
        api = requests.get(specurl).json()
        
        for domainname in [tag['name'] for tag in api['tags']]:
            params = ['_etag', '_pk']
            domainparams = api['paths']['/%s' % domainname]['post']['parameters']
            for param in domainparams:
                params.append(param['name'])
            objecturl = os.path.join(self._baseurl, domainname)
            setattr(self, domainname, ObjectClient(objecturl, Struct(*params, _name=str(domainname))))
    
    def _list_categories(self):
        specurl = os.path.join(self._baseurl, 'docs', 'spec.json')
        api = requests.get(specurl).json()
        return [tag['name'] for tag in api['tags']]
    
def clean(obj):
    for prop in obj.keys():
        if prop.startswith('_') and prop != '_id' and prop != '_meta':
            obj.pop(prop)

class ObjectClient(object):
    def __init__(self, baseurl, objclass):
        self._baseurl = baseurl
        self._objclass = objclass

    def new(self):
        return self._objclass()

    def set(self, obj):
        if isinstance(obj, self._objclass):
            data = obj._dump()
        elif isinstance(obj, dict):
            data = obj.copy()
        else:
            raise ValueError("Invalid object")
        clean(data)
        result = self._parse_response(requests.post(self._baseurl, json=data))
        obj['_pk'] = extract_pk(result['_links'])
        obj['_etag'] = result.get('_etag', None)
        return result

    def get(self, id):
        url = os.path.join(self._baseurl, str(id))
        result = requests.get(url)
        obj = self._parse_response(result)
        return self._objclass(**obj)

    def delete(self, id):
        url = os.path.join(self._baseurl, str(id))
        return self._parse_response(requests.delete(url))
        
    def partialupdate(self, obj):
        if not isinstance(obj, dict):
            raise ValueError("Invalid object")
        url = os.path.join(self._baseurl, obj['_pk'])
        clean(obj)
        return self._parse_response(requests.patch(url, json=obj))

    def _parse_response(self, response):
        if response.status_code >= 300:
            try:
                msg = json.loads(response.text)['_error']['message']
            except:
                msg = response.text
            if response.status_code == 404:
                raise NotFound(msg, statuscode=response.status_code)
            else:
                issues = json.loads(response.text)['_issues']
                msg = "%s : %s" % (msg, issues)
                raise RemoteError(msg, statuscode=response.status_code)
        if response.text:
            return response.json()
        else:
            return None

    def exists(self, id):
        url = os.path.join(self._baseurl, str(id))
        result = requests.head(url)
        try:
            self._parse_response(result)
            return True
        except NotFound:
            return False

    def update(self, obj):
        if isinstance(obj, self._objclass):
            obj = obj._dump()
        if not isinstance(obj, dict):
            raise ValueError("Invalid object")
        if not isinstance(obj, dict):
            raise ValueError("Invalid object")
        url = os.path.join(self._baseurl, str(obj['_pk']))
        headers = {'If-Match': obj['_etag']}
        clean(obj)
        return self._parse_response(requests.put(url, json=obj, headers=headers))

    def list(self):
        query = {'projection': '{"guid": 1}'}
        url = "%s?%s" % (self._baseurl, urllib.urlencode(query))
        results = self._parse_response(requests.get(url))
        return [ x['guid'] for x in results['_items'] ]

    def search(self, query):
        query = {'where': json.dumps(query)}
        url = "%s?%s" % (self._baseurl, urllib.urlencode(query))
        results = self._parse_response(requests.get(url))
        return [ self._objclass(**x) for x in results['_items'] ]
    
    def authenticate(self, username, passwd):
        return True