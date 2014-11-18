from JumpScale import j
import imp
import inspect
from JumpScale.core.system.fs import FileLock

json=j.db.serializers.getSerializerType("j")

OBJECTCLASSES = dict()

class OSISClientForCat():

    def __init__(self, client, namespace, cat):
        self.client = client
        self.namespace = namespace
        self.cat = cat

    def _getModelClass(self):
        key = "%s_%s" % (self.namespace, self.cat)
        if key not in OBJECTCLASSES:
            with FileLock("osis_model_%s_%s" % (self.namespace, self.cat)):
                # if we waited for the lock objectclass might be available now lets check
                if key in OBJECTCLASSES:
                    return OBJECTCLASSES[key]
                retcode,content=self.client.getOsisObjectClassCodeOrSpec(self.namespace,self.cat)
                if retcode==2 or retcode == 1:
                    def getModelClass(module):
                        classes = inspect.getmembers(module, inspect.isclass)
                        complexbase = j.core.osis.getOSISBaseObjectComplexType()
                        simplebase = j.core.osis.getOsisBaseObjectClass()
                        for name, klass in classes:
                            if name != "OsisBaseObject" and issubclass(klass, (complexbase, simplebase)):
                                return klass
                        raise RuntimeError("could not find: class $modelname(OsisBaseObject) in model class file, should always be there")

                    pathdir=j.system.fs.joinPaths(j.dirs.varDir,"code","osis",self.namespace)
                    path=j.system.fs.joinPaths(pathdir,"%s.py" % self.cat)
                    if j.system.fs.exists(path):
                        if j.tools.hash.md5_string(content) != j.tools.hash.md5(path):
                            j.system.fs.remove(path)
                    if not j.system.fs.exists(path):
                        j.system.fs.createDir(pathdir)
                        j.system.fs.writeFile(filename=path,contents=content)
                    try:
                        module = imp.load_source('osis_model_%s_%s' % (self.namespace, self.cat), path)
                    except Exception as e:
                        raise RuntimeError("Could not import osis: %s_%s error:%s"%(self.namespace,self.cat,e))
                    OBJECTCLASSES[key] = getModelClass(module)
                else:
                    raise RuntimeError("Could not find spec or class code for %s_%s on osis"%(self.namespace,self.cat))

        return OBJECTCLASSES[key]

    def authenticate(self, name,passwd,**args):
        """
        authenticates a user and returns the groups in which the user is
        """        
        return  self.client.authenticate(namespace=self.namespace, categoryname=self.cat,name=name,passwd=passwd,**args)     

    def new(self,**args):
        obj=self._getModelClass()(**args)
        obj.init(self.namespace,self.cat,1)
        return obj

    def native(self, methodname, kwargs):
        return self.client.native(namespace=self.namespace, categoryname=self.cat, methodname=methodname, kwargs=kwargs)

    def count(self, query=None):
        return self.client.count(namespace=self.namespace, categoryname=self.cat, query=query)

    def demodata(self):
        """
        populate db with demodata
        """
        return self.client.demodata(namespace=self.namespace, categoryname=self.cat)

    def rebuildindex(self):
        """
        rebuildindex
        """
        return self.client.rebuildindex(namespace=self.namespace, categoryname=self.cat)

    def set(self, obj, key=None,waitIndex=False):
        """
        if key none then key will be given by server
        @return (guid,new,changed)
        """
        # print "WAITINDEX:%s"%waitIndex        
        if hasattr(obj,"dump"):
            obj=obj.dump()
        elif hasattr(obj,"__dict__"):
            obj=obj.__dict__
        return self.client.set(namespace=self.namespace, categoryname=self.cat, key=key, value=obj,waitIndex=waitIndex)

    def get(self, key):        
        value = self.client.get(namespace=self.namespace, categoryname=self.cat, key=key)
        if isinstance(value, str):
            try:
                value=json.loads(value)
            except:
                pass # might be normal string/data aswell
        if isinstance(value, dict):
            klass=self._getModelClass()
            if klass!=None:
                obj=klass(ddict=value)
                # obj.load(value)
                return obj
            else:
                return value
        else:
            return value

    def exists(self, key):            
        return self.client.exists(namespace=self.namespace, categoryname=self.cat, key=key)

    def existsIndex(self,key,timeout=1):            
        return self.client.existsIndex(namespace=self.namespace, categoryname=self.cat, key=key,timeout=timeout)

    def delete(self, key):        
        return self.client.delete(namespace=self.namespace, categoryname=self.cat, key=key)

    def deleteSearch(self,query):
        return self.client.deleteSearch(namespace=self.namespace, categoryname=self.cat, query=query)  
        
    def updateSearch(self,query,update):
        """
        update is dict or text
        dict e.g. {"name":aname,nr:1}  these fields will be updated then
        text e.g. name:aname nr:1
        """
        return self.client.updateSearch(namespace=self.namespace, categoryname=self.cat, query=query,update=update)  

    def destroy(self):
        # self.client.deleteNamespaceCategory(namespacename=self.namespace, name=self.cat)
        return self.client.destroy(namespace=self.namespace, categoryname=self.cat)

    def list(self, prefix=""):
        
        return self.client.list(namespace=self.namespace, categoryname=self.cat, prefix=prefix)

    def search(self, query, start=0, size=None):
        
        return self.client.search(namespace=self.namespace, categoryname=self.cat, query=query,
                                  start=start, size=size)

    def simpleSearch(self, params, start=0, size=None, withguid=False, withtotal=False, sort=None, partials=None, nativequery=None):
        """
        @params is dict with key the propname you look for and the val = val of the prop
        e.g. {"name":name,"country":"belgium"}
        """
        if nativequery:
            query = nativequery.copy()
        else:
            query = {'query': {'bool': {'must': list()}}}
        myranges = {}
        for k, v in params.items():
            if isinstance(v, dict):
                if not v['value']:
                    continue
                if v['name'] not in myranges:
                    myranges = {v['name']: dict()}
                myranges[v['name']] = {v['eq']: v['value']}
            elif v:
                if isinstance(v, str):
                    # v = v.lower()
                    pass
                term = {'term': {k: v}}
                query['query']['bool']['must'].append(term)
        for key, value in myranges.items():
            query['query']['bool']['must'].append({'range': {key: value}})
        if partials:
            query['query']['bool']['must'].append({'wildcard': partials})
        boolq = query.get('query', {}).get('bool', {})
        def isEmpty(inputquery):
            for key, value in inputquery.items():
                if value:
                    return False
            return True

        if isEmpty(boolq):
            query = nativequery or dict()
        if sort:
            query['sort'] = [ {x:v} for x,v in sort.items() ]

        response = self.search(query, start, size)

        results = list()
        if isinstance(response, list): # mongo client
            if not response:
                return 0, response
            total = response.pop(0)
            for r in response:
                r.pop('_meta', None)
                results.append(r)
            if withtotal:
                return total, results
            else:
                return results
        elif isinstance(response, dict): # ES client:
            if 'result' in response:
                rawresults = response['result']
            elif 'hits' in response:
                rawresults = response['hits']['hits']
            for item in rawresults:
                if withguid:
                    item['_source']['guid'] = item['_id']
                results.append(item['_source'])
            if not withtotal:
                return results
            else:
                total = -1
                if 'total' in response:
                    total = response['total']
                elif 'hits' in response and 'total' in response['hits']:
                    total = response['hits']['total']
                return total, results
