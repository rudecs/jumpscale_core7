from JumpScale import j
from .ServiceTemplate import ServiceTemplate
from .Service import Service, getProcessDicts
from .RemoteService import RemoteService
import re
from .ActionsBase import ActionsBase
import AYSdb
import json
import os

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
            repos=j.do.getGitReposListLocal(errorIfNone=False)
            pullrepos = 'AYS_RO' not in os.environ
            for domain, repo in items.iteritems():
                url=repo['url']
                branch = repo.get('branch') or None
                tag = repo.get('tag') or None
                if not tag and not branch:
                    branch = 'master'
                reponame=url.rpartition("/")[-1]
                if reponame not in repos.keys() and pullrepos:
                    #means git has not been pulled yet
                    if login!="":
                        dest=j.do.pullGitRepo(url,dest=None,login=login,passwd=passwd,depth=1,ignorelocalchanges=False,reset=False,branch=branch, tag=tag)
                    else:
                        dest=j.do.pullGitRepo(url,dest=None,depth=1,ignorelocalchanges=False,reset=False,branch=branch, tag=tag)
                    repos=j.do.getGitReposListLocal()
                if reponame in repos:
                    dest=repos[reponame]
                    self.domains[domain]=dest

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
            branch = repo.get('branch') or None
            tag = repo.get('tag') or None
            if not tag and not branch:
                branch = 'master'
            j.do.pullGitRepo(url=repo['url'], branch=branch, tag=tag)

    def updateExternalRepos(self, repos=[]):
        """
        update the git repo that contains the external services
        args:
            repos : list of dict of repos to update, if empty, all repos are updated
                    {
                        'url' : 'http://github.com/account/repo',
                        'branch' : 'master'
                    }
        """
        if len(repos) == 0:
            metadata = j.application.config.getDictFromPrefix('atyourservice.ays')
            repos = metadata.values()

        destinations = dict()
        for repo in repos:
            type = 'git'
            _, account, reponame = repo.get('url', '/').rstrip('.git').rsplit('/', 2)
            branch = repo.get('branch') or None
            tag = repo.get('tag') or None
            if not tag and not branch:
                branch = 'master'
            dest = '/tmp/%s/%s/%s/' % (type, account, reponame)
            j.do.pullGitRepo(url=repo['url'], branch=branch, dest=dest, tag=tag)
            destinations[repo.get('name', reponame)] = dest

        return destinations

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

    def findServices(self, domain="", name="", instance="", parent='', precise=False, hrdReset=None):
        """
        FindServices looks for actual services that are created
        """
        def createService(domain, name, instance, path, parent=None, hrdReset=None):
            # try to load service from instance file is they exists
            hrdpath = j.system.fs.joinPaths(path, "service.hrd")
            actionspath = j.system.fs.joinPaths(path, "actions.py")
            parents = self.findParents(path=path) if (not parent and path) else [parent]
            parent = parents[0] if isinstance(parents, list) and parents else (parent if parent else None)

            # create service from templates
            servicetemplates = self.findTemplates(domain=domain, name=name)
            if len(servicetemplates) > 0:
                remote = [p for p in parents if 'node' in p.categories]
                if remote:
                    remote = remote[-1]
                    service = RemoteService(instance=instance, servicetemplate=servicetemplates[0], path=path, parent=parent,
                                            remotecategory=remote.categories[0], remoteinstance=remote.instance)
                else:
                    service = Service(instance=instance, servicetemplate=servicetemplates[0], path=path, parent=parent, hrdReset=hrdReset)
                return service
            # create service from action.py and service.hrd
            elif j.system.fs.exists(hrdpath) and j.system.fs.exists(actionspath):
                service = j.atyourservice.loadService(path, parent)
                return service
            else:
                raise RuntimeError("Cannot find service %s__%s__%s" % (domain, name, instance))

        parentregex = '.*'
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
        serviceregex = "%s__%s__%s" % (domain if domain.strip() else '[a-zA-Z0-9_\.-]*',
                                        name if name.strip() else '[a-zA-Z0-9_\.-]*',
                                        instance if instance.strip() else '[a-zA-Z0-9_\.-]*')
        preciseregex = '.*' if parent is not None else ''

        startregex = j.dirs.getHrdDir().rstrip('/').replace('/', '.')

        servicekey = '%s/%s%s%s$' % (startregex, parentregex, preciseregex, serviceregex)
        regex = re.compile(servicekey)
        matched = [m.string for path in candidates for m in [regex.search(path)] if m]

        for path in matched:
            domainfoud, namefound, instancefound = j.system.fs.getBaseName(path).split('__')
            service = createService(domainfoud, namefound, instancefound, path, parent, hrdReset=hrdReset)
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

    def new(self, domain="", name="", instance="main", path=None, parent=None, args={}, hrdSeed=None):
        """
        will create a new service
        """
        self._doinit()
        serviceTmpls = self.findTemplates(domain, name)

        if len(serviceTmpls) == 0:
            raise RuntimeError("cannot find service template %s__%s" % (domain, name))
        obj = serviceTmpls[0].newInstance(instance, path=path, parent=parent, args=args, precise=True, hrdSeed=hrdSeed)
        return obj

    def remove(self, domain="", name="", instance="", parent=None):
        services = self.findServices(domain, name, instance, parent)
        for s in services:
            j.system.fs.removeDirTree(s.path)
            id = self.getId(s.domain, s.name, s.instance, parent)
            if id in self._instanceCache:
                del(self._instanceCache[id])

    def get(self, domain="", name="", instance="", parent='', precise=False):
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
        remote = [p for p in j.atyourservice.findParents(path=fullpath) if 'node' in p.categories]
        if remote:
            remote = remote[-1]
            service = RemoteService(domain=hrd.get('service.domain', hrd.get('domain', '')),
                                    name=hrd.get('service.name', hrd.get('name', '')),
                                    instance=hrd.get('service.instance', hrd.get('instance', '')),
                                    hrd=hrd, path=path, parent=parent,
                                    remotecategory=remote.categories[0], remoteinstance=remote.instance)
        else:
            service = Service(domain=hrd.get('service.domain', hrd.get('domain', '')),
                              name=hrd.get('service.name', hrd.get('name', '')),
                              instance=hrd.get('service.instance', hrd.get('instance', '')),
                              hrd=hrd, path=path, parent=parent)

        service.init()
        return service

    def loadAYSInSQL(self):
        """
        walk over all services and load into sqllite
        """

        def _loadHRDItems(hrddict, hrd, objectsql):
            hrds = list()
            recipes = list()
            processes = list()
            dependencies = list()
            for key, value in hrddict.items():
                if key.startswith('service.process'):
                    continue
                elif key.startswith('process'):
                    processsql = AYSdb.Process()
                    if key == 'ports':
                        ports = list()
                        for port in value:
                            tcpportsql = AYSdb.TCPPort(tcpport=port)
                            sql.session.add(tcpportsql)
                            ports.append(tcpportsql)
                        processsql.ports = ports
                    elif key == 'env':
                        processsql.env = json.dumps(value)
                    else:
                        processsql.__setattr__(key, value)
                    sql.session.add(processsql)
                    processes.append(processsql)
                elif key.startswith('git.export') or key.startswith('service.web.export'):
                    recipesql = AYSdb.RecipeItem()
                    recipesql.order = key.split('export.', 1)[1]
                    recipesql.recipe = json.dumps(value)
                    sql.session.add(recipesql)
                    recipes.append(recipesql)
                elif key.startswith("service.dependencies") or key.startswith('dependencies'):
                    if not isinstance(value, list):
                        value = [value]
                    for val in value:
                        dependencysql = AYSdb.Dependency()
                        dependencysql.order = key.split('dependencies.', 1)[1] if key.startswith('dependencies.') else '1'
                        dependencysql.domain = val.get('domain', '')
                        dependencysql.name = val.get('name', '')
                        dependencysql.instance = val.get('instance', '')
                        dependencysql.args = json.dumps(val.get('args', '{}'))
                        sql.session.add(dependencysql)
                        dependencies.append(dependencysql)
                else:
                    hrdsql = AYSdb.HRDItem()
                    hrdsql.key = key
                    hrdsql.value = json.dumps(value)
                    hrdsql.isTemplate = True
                    sql.session.add(hrdsql)
                    hrds.append(hrdsql)

            objectsql.hrd = hrds
            objectsql.processes = processes
            objectsql.recipes = recipes
            objectsql.dependencies = dependencies

        sqlitepath = j.dirs.varDir+"/AYS.db"

        # Delete previously loaded AYS objects
        j.system.fs.remove(sqlitepath)

        sql = j.db.sqlalchemy.get(sqlitepath=sqlitepath, tomlpath=None, connectionstring='')

        if not self._init:
            self._doinit()
        templates = {'local': self.findTemplates()}
        services = {'local': self.findServices()}

        destinations = self.updateExternalRepos()
        for destname, dest in destinations.items():
            cservices = j.system.fs.joinPaths(dest, 'services')
            ctemplates = j.system.fs.joinPaths(dest, 'servicetemplates')
            for service in j.system.fs.listDirsInDir(cservices):
                domain, name, instance = j.system.fs.getBaseName(service).split('__')
                ctemplate = ServiceTemplate(domain, name, None, parent=None)
                cservice = ctemplate.newInstance(instance=instance, path=service)
                if destname not in services:
                    services[destname] = list()
                services[destname].append(cservice)

            for domain in j.system.fs.listDirsInDir(ctemplates):
                for name in j.system.fs.listDirsInDir(domain):
                    ctemplate = ServiceTemplate(j.system.fs.getBaseName(domain), j.system.fs.getBaseName(name), name, parent=None)
                    if destname not in templates:
                        templates[destname] = list()
                    templates[destname].append(ctemplate)


        attributes = ('domain', 'name', 'metapath')
        for templatetype, templates in templates.items():
            for template in templates:
                templatesql = AYSdb.Template()
                for attribute in attributes:
                    templatesql.__setattr__(attribute, template.__getattribute__(attribute))

                instances = list()
                for instance in template.listInstances():
                    instancesql = AYSdb.Instance(instance=instance)
                    sql.session.add(instancesql)
                    instances.append(instancesql)
                templatesql.instancehrd = template.getInstanceHRD()
                templatesql.instances = instances
                templatesql.type = templatetype
                hrd = template.getHRD()
                hrddict = hrd.getHRDAsDict()

                _loadHRDItems(hrddict, hrd, templatesql)
                sql.session.add(templatesql)

        for servicetype, serviceslist in services.items():
            children = list()
            for service in serviceslist + children:
                parentsql = None
                if isinstance(service.parent, Service):
                    parent = sql.session.query(AYSdb.Service).filter_by(domain=service.parent.domain, name=service.parent.name,
                                                                 instance=service.parent.instance, path=service.parent.path).all()
                    if not parent:
                        children.append(service)
                        continue
                    else:
                        parentsql = parent[0].id

                servicesql = AYSdb.Service()
                attributes = ('domain', 'name', 'instance', 'path', 'noremote', 'templatepath',
                              'cmd')

                for attribute in attributes:
                    servicesql.__setattr__(attribute, service.__getattribute__(attribute))

                hrddict = service.hrd.getHRDAsDict()
                _loadHRDItems(hrddict, service.hrd, servicesql)

                servicesql.parent = parentsql
                servicesql.priority = service.getPriority()
                servicesql.logPath = service.getLogPath()
                servicesql.isInstalled = service.isInstalled()
                servicesql.isLatest = service.isLatest()

                servicesql.type = servicetype

                producers = list()
                for key, value in service.producers.items():
                    producersql = AYSdb.Producer(key=key, value=value)
                    sql.session.add(producersql)
                    producers.append(producersql)
                servicesql.producer = producers

                categories = list()
                for category in service.categories:
                    categorysql = AYSdb.Category(category=category)
                    sql.session.add(categorysql)
                    categories.append(categorysql)
                servicesql.category = categories

                processes = list()
                procs = getProcessDicts(hrd)
                for process in procs:
                    processsql = AYSdb.Process()
                    for key, value in process.items():
                        if key == 'ports':
                            ports = list()
                            for port in value:
                                tcpportsql = AYSdb.TCPPort(tcpport=port)
                                sql.session.add(tcpportsql)
                                ports.append(tcpportsql)
                            processsql.ports = ports
                        elif key == 'env':
                            processsql.env = json.dumps(value)
                        else:
                            processsql.__setattr__(key, value)
                    sql.session.add(processsql)
                    processes.append(processsql)
                servicesql.processes = processes

                servicesql.children = json.dumps(service.listChildren())

                sql.session.add(servicesql)
        sql.session.commit()

    def getServicefromSQL(self, serviceid=None, domain=None, name=None, instance=None, reload=False):
        if reload:
            self.loadAYSInSQL()

        from JumpScale.baselib.atyourservice import AYSdb
        sql = j.db.sqlalchemy.get(sqlitepath=j.dirs.varDir+"/AYS.db", tomlpath=None, connectionstring='')

        if serviceid is not None:
            result = [sql.session.query(AYSdb.Service).get(serviceid)]
        elif domain or name or instance:
            kwargs = {argname:argvalue for argname, argvalue in {'domain':domain, 'name':name, 'instance':instance}.items() if argvalue != None}
            result = sql.session.query(AYSdb.Service).filter_by(**kwargs).all()
        else:
            result = sql.session.query(AYSdb.Service).all()
        return result
        
    def getTemplatefromSQL(self, templateid=None, domain=None, name=None, metapath=None, reload=False):
        if reload:
            self.loadAYSInSQL()

        from JumpScale.baselib.atyourservice import AYSdb
        sql = j.db.sqlalchemy.get(sqlitepath=j.dirs.varDir+"/AYS.db", tomlpath=None, connectionstring='')

        if templateid is not None:
            result = [sql.session.query(AYSdb.Template).get(templateid)]
        elif domain or name or metapath:
            kwargs = {argname:argvalue for argname, argvalue in {'domain':domain, 'name':name, 'metapath':metapath}.items() if argvalue != None}
            result = sql.session.query(AYSdb.Template).filter_by(**kwargs).all()
        else:
            result = sql.session.query(AYSdb.Template).all()
        return result
        

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
