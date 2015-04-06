from JumpScale import j
from .ServiceTemplate import ServiceTemplate
from .Service import Service
import copy
from .ActionsBase import ActionsBase

class AtYourServiceFactory():

    def __init__(self):

        self._init=False
        self.domains={}
        self.hrd=None
        self._justinstalled=[]
        self._type = None
        self._cachefind={}
        self._cache={}

        self.indocker=False

    @property
    def type(self):
        self._type="n" #n from normal
        #check if we are in a git directory, if so we will use $thatdir/service as base for the metadata
        configpath=j.dirs.amInGitConfigRepo()
        if configpath!=None:
            self._type="c"
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

    def getActionsBaseClass(self):
        return ActionsBase

    def getDomains(self):
        return self.domains.keys()


    def findTemplates(self,domain="",name=""):
        key="%s__%s"%(domain,name)
        if self._cachefind.has_key(key):
            return self._cachefind[key]

        self._doinit()

        #create some shortcuts for fast return
        if domain!="":
            if domain not in self.domains:
                return[]
            if name!="":
                path = j.system.fs.joinPaths(self.domains[domain],name)
                if not j.system.fs.exists(path=path):
                    return []

        baseDomains=j.application.config.getDictFromPrefix("jpackage.metadata")
        def sorter(domain1,domain2):
            if domain1 in baseDomains:
                return 1
            return -1

        res = []
        for domainfound in sorted(self.domains.keys(), cmp=sorter):
            for path in j.system.fs.listDirsInDir(path=self.domains[domainfound], recursive=True, dirNameOnly=False, findDirectorySymlinks=True):
                namefound=j.system.fs.getBaseName(path)

                if path.find("/.git")!=-1:
                    continue

                #TEMP untill upgraded
                if j.system.fs.exists(path="%s/%s"%(path,"jp.hrd")):
                    j.system.fs.renameFile("%s/%s"%(path,"jp.hrd"),"%s/%s"%(path,"service.hrd"))

                if not j.system.fs.exists(path="%s/%s"%(path,"service.hrd")):
                    continue
                if domain=="" and name=="":
                    if namefound not in res:
                        res.append((domainfound,namefound,path))
                elif domain=="" and name!="":
                    if namefound==name:
                        if namefound not in res:
                            res.append((domainfound,namefound,path))
                elif domain!="" and name=="":
                    if domain==domainfound:
                        if namefound not in res:
                            res.append((domainfound,namefound,path))
                else:
                    if domain==domainfound and namefound.find(name)==0:
                        if namefound not in res:
                            res.append((domainfound,namefound,path))

        finalRes=[]
        for domain,name,path in res:
            finalRes.append(ServiceTemplate(domain,name,path))

        self._cachefind[key]=finalRes
        return finalRes


    def findServices(self,domain="",name="",instance=""):
        """
        FindServices looks for actual services that are created
        """
        def createService(domain,name,instance,path):
                    targetKey="%s__%s__%s"%(domain,name,instance)
                    if name!="" and instance!="" and self._cache.has_key(targetKey):
                        return self._cache[targetKey]

                    servicetemplates=self.findTemplates(domain=domain,name=name)
                    if len(servicetemplates) <= 0:
                        raise RuntimeError("services template %s__%s not found"%(domain,name))
                    service=Service(instance=instance,servicetemplate=servicetemplates[0],path=path)
                    if name!="" and instance!="":
                        self._cache[targetKey]=service
                    return service

        targetKey="%s__%s__%s"%(domain,name,instance)
        if name!="" and instance!="":
            if self._cachefind.has_key(targetKey):
                return self._cachefind[targetKey]

        self._doinit()

        res=[]
        for path in j.system.fs.listDirsInDir(j.dirs.hrdDir, recursive=True, dirNameOnly=False, findDirectorySymlinks=True):
            namefound=j.system.fs.getBaseName(path)

            # if the directory name has not the good format, skip it
            if namefound.find("__")==-1:
                continue

            namefound,instancefound=namefound.split("__",1)
            service=None
            if instance=="" and name=="":
                service =createService(domain,namefound,instancefound,path)
            elif instance=="" and name!="":
                if namefound==name:
                    service = createService(domain,namefound,instancefound,path)
            elif instance!="" and name=="":
                if instance==instancefound:
                    service = createService(domain,namefound,instancefound,path)
            elif instance==instancefound and namefound == name:
                    service = createService(domain,namefound,instancefound,path)
            if service != None:
                res.append(service)

        if name!="" and instance!="":
            self._cachefind[targetKey]=res
        return res


    def findParents(self,service,name=""):

        path=service.path
        basename=j.system.fs.getBaseName(path)
        res=[]
        while True:
            path=j.system.fs.getParent(path)
            basename=j.system.fs.getBaseName(path)
            if basename=="services" or basename=="apps":
                break

            ss = basename.split("__")
            parentName = ss[0]
            parentInstance = ss[1]
            service = self.get(name=parentName,instance=parentInstance)
            if name!="" and service.name == name:
                return service
            res.append(service)
        return res

    def new(self,domain="",name="",instance="main",parent=None,args={}):
        """
        will create a new service
        """
        serviceTmpls=None
        key="%s__%s__%s"%(domain,name,instance)
        if self._cache.has_key(key):
             serviceTmpls = self._cache[key]

        self._doinit()

        serviceTmpls=self.findTemplates(domain,name)
        if len(serviceTmpls)==0:
            raise RuntimeError("cannot find service template %s__%s"%(domain,name))
        obj=serviceTmpls[0].newInstance(instance,parent=parent, args=args)
        self._cache[key]=obj
        return obj

    def get(self,domain="",name="",instance=""):
        """
        Return service indentifier by domain,name and instance
        throw error if service is not found or if more than one service is found
        """
        key="%s__%s__%s"%(domain,name,instance)
        if self._cache.has_key(key):
            return self._cache[key]
        self._doinit()
        services=self.findServices(domain,name,instance=instance)
        if len(services)==0:
            raise RuntimeError("cannot find service %s__%s"%(domain,name))
        if len(services)>1:
            raise RuntimeError("multiple service found, be more precise %s%s"%(domain,name))
        self._cache[key]=services[0]
        return self._cache[key]


    # def exists(self,domain="",name="",instance=""):
    #     self._doinit()
    #     tmpls=self.findTemplates(domain,name)
    #     if len(tmpls)==0:
    #         return False
    #     from ipdb import set_trace;set_trace()
    #     return  tmpls[0].existsInstance(instance)

    def __str__(self):
        return self.__repr__()
