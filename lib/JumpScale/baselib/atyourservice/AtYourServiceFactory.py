from JumpScale import j
from .ServiceTemplate import ServiceTemplate
from .Service import Service
from .RemoteService import RemoteService
import re
from .ActionsBase import ActionsBase

class AtYourServiceFactory():

    def __init__(self):

        self._init=False
        self.domains={}
        self.hrd=None
        self._justinstalled=[]
        self._type = None
        self._instanceCache = {}
        self._templateCache = {}

        self.indocker=False

    @property
    def type(self):
        self._type="n" #n from normal
        #check if we are in a git directory, if so we will use $thatdir/services as base for the metadata
        configpath=j.dirs.amInGitConfigRepo()
        if configpath!=None:
            self._type="c"
            j.system.fs.createDir(j.dirs.hrdDir)
        return self._type

    @type.setter
    def type(self, value):
        self._type=value

    def _doinit(self):

        if self._init==False:
            j.do.debug=False

            if j.system.fs.exists(path="/etc/my_init.d"):
                self.indocker=True

            login=j.application.config.get("whoami.git.login").strip()
            passwd=j.application.config.getStr("whoami.git.passwd").strip()

            if self.type != "n":
                configpath=j.dirs.amInGitConfigRepo()
                self.domains[j.system.fs.getBaseName(configpath)]="%s/servicetemplates/"%configpath

            # always load base domaim
            items=j.application.config.getDictFromPrefix("atyourservice.metadata")
            repos=j.do.getGitReposListLocal()
            for domain in items.keys():
                url=items[domain]['url']
                branch=items[domain].get('branch', 'master')
                reponame=url.rpartition("/")[-1]
                if not reponame in repos.keys():
                    #means git has not been pulled yet
                    if login!="":
                        dest=j.do.pullGitRepo(url,dest=None,login=login,passwd=passwd,depth=1,ignorelocalchanges=False,reset=False,branch=branch)
                    else:
                        dest=j.do.pullGitRepo(url,dest=None,depth=1,ignorelocalchanges=False,reset=False,branch=branch)

                repos=j.do.getGitReposListLocal()

                dest=repos[reponame]
                self.domains[domain]=dest

            self_init=True


    def updateTemplatesRepo(self, repos=[]):
        """
        update the git repo that contains the service templates
        args:
            repos : list of dict of repos to update, if empty, all repos are updated
                    {
                        'url' : 'http://github.com/account/repo',
                        'branch' : 'master'
                    }
        """
        if len(repos) == 0:
            metadata = j.application.config.getDictFromPrefix('atyourservice.metadata')
            repos = metadata.values()

        for repo in repos:
            branch = repo['branch'] if 'branch' in repo else 'master'
            j.do.pullGitRepo(url=repo['url'], branch=branch)

    def getActionsBaseClass(self):
        return ActionsBase

    def getDomains(self):
        return self.domains.keys()

    def getId(self, domain, name, instance, parent=None):
        str_parent = "none"
        if parent is not None:
            # if not isinstance(parent, Service):
            #     j.events.opserror_critical("parent should be of type JumpScale.baselib.atyourservice.Service.Service\nit's %s" % type(parent))
            str_parent = str(parent).replace('  ', '')

        return "%s__%s__%s__%s" % (domain, name, instance, str_parent)

    def findTemplates(self, domain="", name="", parent=None):
        key = "%s__%s" % (domain, name)
        if key in self._templateCache:
            return self._templateCache[key]

        self._doinit()

        # create some shortcuts for fast return
        if domain != "":
            if domain not in self.domains:
                return[]

        baseDomains = j.application.config.getDictFromPrefix("atyourservice.metadata")

        def sorter(domain1, domain2):
            if domain1 in baseDomains:
                return 1
            return -1

        res = []
        for domainfound in sorted(self.domains.keys(), cmp=sorter):
            for path in j.system.fs.walk(self.domains[domainfound], recurse=1, return_folders=1, return_files=0, followSoftlinks=True):
                namefound = j.system.fs.getBaseName(path)

                if path.find("/.git") != -1:
                    continue

                if not j.system.fs.exists(path="%s/%s" % (path, "service.hrd")):
                    continue
                if domain != '' and domain != domainfound:
                    continue
                if name != '' and name != namefound:
                    continue
                if namefound not in res:
                    res.append((domainfound, namefound, path))

        finalRes = []
        for domain, name, path in res:
            finalRes.append(ServiceTemplate(domain, name, path, parent))

        self._templateCache[key] = finalRes
        return finalRes

    def findServices(self, domain="", name="", instance="", parent=None, precise=False):
        """
        FindServices looks for actual services that are created
        """
        def createService(domain, name, instance, path, parent=None):
            # try to load service from instance file is they exists
            hrdpath = j.system.fs.joinPaths(path, "service.hrd")
            actionspath = j.system.fs.joinPaths(path, "actions.py")
            parents = self.findParents(path=path) if (not parent and path) else [parent]
            parent = parents[0] if isinstance(parents, list) and parents else (parent if parent else None)

            # create service from templates
            servicetemplates = self.findTemplates(domain=domain, name=name)
            if len(servicetemplates) > 0:
                remote = any(['node' in p.categories for p in parents])
                if remote:
                    service = RemoteService(instance=instance, servicetemplate=servicetemplates[0], path=path, parent=parent)
                else:
                    service = Service(instance=instance, servicetemplate=servicetemplates[0], path=path, parent=parent)
                return service
            # create service from action.py and service.hrd
            elif j.system.fs.exists(hrdpath) and j.system.fs.exists(actionspath):
                service = j.atyourservice.loadService(path, parent)
                return service
            else:
                raise RuntimeError("Cannot find service %s__%s__%s" % (domain, name, instance))

        parentregex = ''
        if parent and isinstance(parent, (Service, RemoteService)):
            parentregex = '%s__%s__%s' % (parent.domain, parent.name, parent.instance)
        elif parent and isinstance(parent, basestring):
            parentregex = parent.replace(':', '.')
            # get only last parent
            parentdata = parent.replace(':', '__').split('__')
            pdomain, pname, pinstance = parentdata[-3:]
            parent = self.findServices(pdomain, pname, pinstance, parent='__'.join(parentdata[:-3]), precise=precise)
            parent = parent[0] if parent else None

        targetKey = self.getId(domain, name, instance, parent)
        if targetKey in self._instanceCache:
            return [self._instanceCache[targetKey]]

        self._doinit()

        res = []
        candidates = j.system.fs.walk(j.dirs.getHrdDir(), recurse=1, pattern='*__*__*', return_folders=1, return_files=0, followSoftlinks=True)
        serviceregex = "%s__%s__%s" % (domain if domain.strip() else '[a-zA-Z0-9_\.]*',
                                        name if name.strip() else '[a-zA-Z0-9_\.]*',
                                        instance if instance.strip() else '[a-zA-Z0-9_\.]*')
        preciseregex = '.*' if not precise else '.'

        startregex = '.*'
        if precise and not parent:
            startregex = j.dirs.getHrdDir().rstrip('/').replace('/', '.')

        servicekey = '%s%s%s%s$' % (startregex, parentregex, preciseregex, serviceregex)
        regex = re.compile(servicekey)
        matched = [m.string for path in candidates for m in [regex.search(path)] if m]

        for path in matched:
            domainfoud, namefound, instancefound = j.system.fs.getBaseName(path).split('__')
            service = createService(domainfoud, namefound, instancefound, path, parent)
            res.append(service)
            self._instanceCache[service.id] = service

        return res

    def findParents(self, service=None, name='', path='', limit=None):
        path = service.path if service else path
        if not path:
            return []
        basename = j.system.fs.getBaseName(path)
        res = []
        while True:
            if limit and len(res) >= limit:
                return res
            path = j.system.fs.getParent(path)
            basename = j.system.fs.getBaseName(path)
            if basename == "services" or basename == "apps":
                break

            ss = basename.split("__")
            domainName = ss[0]
            parentName = ss[1]
            parentInstance = ss[2]
            service = self.get(domain=domainName, name=parentName, instance=parentInstance)
            if name != "" and service.name == name:
                return [service]
            res.append(service)
        return res

    def findProducer(self, producercategory, instancename):
        for item in self.findServices(instance=instancename):
            if producercategory in item.categories:
                return item

    def new(self, domain="", name="", instance="main", path=None, parent=None, args={}):
        """
        will create a new service
        """
        self._doinit()
        serviceTmpls = self.findTemplates(domain, name)

        if len(serviceTmpls) == 0:
            raise RuntimeError("cannot find service template %s__%s" % (domain, name))
        obj = serviceTmpls[0].newInstance(instance, path=path, parent=parent, args=args, precise=True)
        return obj

    def remove(self, domain="", name="", instance="", parent=None):
        services = self.findServices(domain, name, instance, parent)
        for s in services:
            j.system.fs.removeDirTree(s.path)
            id = self.getId(s.domain, s.name, s.instance, parent)
            if id in self._instanceCache:
                del(self._instanceCache[id])

    def get(self, domain="", name="", instance="", parent=None, precise=False):
        """
        Return service indentifier by domain,name and instance
        throw error if service is not found or if more than one service is found
        """
        services = None
        key = self.getId(domain, name, instance, parent)
        if key in self._instanceCache:
            services = self._instanceCache[key]
            if parent is None or (len(services) == 1 and services[0].parent == parent):
                return services
            else:
                services = None
        if services is None:
            self._doinit()
            services = self.findServices(domain=domain, name=name, instance=instance, parent=parent, precise=precise)

        if len(services) == 0:
            raise RuntimeError("cannot find service %s__%s__%s" % (domain, name, instance))
        if len(services) > 1:
            raise RuntimeError("multiple service found :\n[%s]\n, be more precise %s%s"%(',\n'.join([str(s) for s in services]), domain,name))
        return services[0]

    def loadService(self,path, parent=None):
        """
        Load a service instance from files located at path.
        path should point to a directory that contains these files:
            service.hrd
            actions.py
        """
        hrdpath = j.system.fs.joinPaths(path, "service.hrd")
        actionspath = j.system.fs.joinPaths(path, "actions.py")
        if not j.system.fs.exists(hrdpath) or not j.system.fs.exists(actionspath):
            raise RuntimeError("path doesn't contain service.hrd and actions.py")

        hrd = j.core.hrd.get(hrdpath, prefixWithName=False)
        fullpath = path or ('%s/domain__name__instance' % parent.path if parent else '')
        remote = any(['node' in p.categories for p in j.atyourservice.findParents(path=path)])
        if remote:
            service = RemoteService(domain=hrd.get('service.domain', hrd.get('domain', '')),
                                    name=hrd.get('service.name', hrd.get('name', '')),
                                    instance=hrd.get('service.instance', hrd.get('instance', '')),
                                    hrd=hrd, path=path, parent=parent)
        else:
            service = Service(domain=hrd.get('service.domain', hrd.get('domain', '')),
                              name=hrd.get('service.name', hrd.get('name', '')),
                              instance=hrd.get('service.instance', hrd.get('instance', '')),
                              hrd=hrd, path=path, parent=parent)

        service.init()
        return service

    def getFromStr(self, representation, parent=None):
        """
        return a service instance from its representation 'domain      :name       :instance'
        """
        ss = [r.strip() for r in representation.split(':')]
        if len(ss) != 3:
            return None
        return j.atyourservice.get(domain=ss[0], name=ss[1], instance=ss[2],parent=parent)
    # def exists(self,domain="",name="",instance=""):
    #     self._doinit()
    #     tmpls=self.findTemplates(domain,name)
    #     if len(tmpls)==0:
    #         return False
    #     from ipdb import set_trace;set_trace()
    #     return  tmpls[0].existsInstance(instance)

    def __str__(self):
        return self.__repr__()
