import requests
import urllib
import os
import json


class NotFound(Exception):
    pass

class ModelObject(object):
    def _dump(self):
        result = dict()
        for slot in self.__slots__:
            result[slot] = getattr(self, slot)
        return result

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
            link = ikwargs['_links']['self']['href']
            self._pk = link.split('/')[-1]

    name = kwargs.pop("_name", "MyStruct")
    kwargs.update(dict((k, None) for k in args))
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

class NameSpaceClient(object):
    def __init__(self, baseurl):
        self._baseurl = baseurl
        self._load_namespace()

    def _load_namespace(self):
        specurl = os.path.join(self._baseurl, 'docs', 'spec.json')
        api = requests.get(specurl).json()
        for domainname, domain in api['domains'].iteritems():
            params = ['_etag', '_pk']
            domainparams = domain['/%s' % domainname]['POST']['params']
            for param in domainparams:
                params.append(param['name'])
            objecturl = os.path.join(self._baseurl, domainname)
            setattr(self, domainname, ObjectClient(objecturl, Struct(*params, _name=str(domainname))))
        pass

def clean(obj):
    for prop in obj.keys():
        if prop.startswith('_') and prop != '_id':
            obj.pop(prop)

class ObjectClient(object):
    def __init__(self, baseurl, objclass):
        self._baseurl = baseurl
        self._objclass = objclass

    def new(self):
        return self._objclass()

    def set(self, obj):
        if isinstance(obj, self._objclass):
            obj = obj._dump()
        if not isinstance(obj, dict):
            raise ValueError("Invalid object")
        clean(obj)
        return requests.post(self._baseurl, json=obj).json()

    def get(self, id):
        url = os.path.join(self._baseurl, str(id))
        result = requests.get(url)
        if result.status_code == 404:
            raise NotFound(result.json()['_error']['message'])
        obj = result.json()
        return self._objclass(**obj)

    def delete(self, id):
        url = os.path.join(self._baseurl, str(id))
        return requests.delete(url).json()

    def partialupdate(self, obj):
        if not isinstance(obj, dict):
            raise ValueError("Invalid object")
        url = os.path.join(self._baseurl, obj['_pk'])
        clean(obj)
        return requests.patch(url, json=obj).json()

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
        return requests.put(url, json=obj, headers=headers).json()

    def list(self):
        query = {'projection': '{"guid": 1}'}
        url = "%s?%s" % (self._baseurl, urllib.urlencode(query))
        results = requests.get(url).json()
        return [ x['guid'] for x in results['_items'] ]

    def search(self, query):
        query = {'where': json.dumps(query)}
        url = "%s?%s" % (self._baseurl, urllib.urlencode(query))
        results = requests.get(url).json()
        return [ self._objclass(**x) for x in results['_items'] ]


