from JumpScale import j
from .ServiceTemplate import ServiceTemplate

from .ActionsBase import ActionsBase

class AtYourServiceFactory():

    def __init__(self):

        self._init=False
        self.domains={}
        self.hrd=None
        self._justinstalled=[]
        self._type = None

        self.indocker=False

    @property
    def type(self):
        self._type="n" #n from normal
        #check if we are in a git directory, if so we will use $thatdir/jp as base for the metadata
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
            items=j.application.config.getDictFromPrefix("jpackage.metadata")
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


    def find(self,domain="",name="",maxnr=None,instance=""):
        #lets ignore domain when instance is known, this could be issue but lets try
        if instance!="":
            res=[]
            for path in j.system.fs.listDirsInDir(j.dirs.hrdDir, recursive=True, dirNameOnly=False, findDirectorySymlinks=True):
                namefound=j.system.fs.getBaseName(path)
                name,instance=namefound.split("__",1)
                instance=instance.split(".",1)[0]
                res.append(Service(namefound,instance,path))
            return res

        else:
            #we look for service template
            self._doinit()
                    
            #create some shortcuts for fast return
            if domain!="":
                if domain not in self.domains:
                    return[]
                if name!="":
                    if not j.system.fs.exists(path="%s/%s"%(self.domains[domain],name)):
                        return []

            baseDomains=j.application.config.getDictFromPrefix("jpackage.metadata")
            def sorter(domain1,domain2):
                if domain1 in baseDomains:
                    return 1
                return -1

            res = []
            items=j.application.config.getDictFromPrefix("jpackage.metadata")
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
                        if namefound.find(name)==0: #match beginning of str so can do search like node.
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
            for domainfound,namefound,path in res:
                finalRes.append(ServiceTemplate(domainfound,namefound,path))
            #now name & domain is known
            if maxnr!=None and len(finalRes)>maxnr:
                j.events.inputerror_critical("Found more than %s jpackage for query '%s':'%s'"%(maxnr,domain,name))

            return finalRes

    def new(self,domain="",name="",instance="main",args={}, hrddata=None):
        """
        will create a new service 
        """
        self._doinit()
        services=self.find(domain,name,1)
        if len(services)==0:
            j.events.opserror_critical("cannot find jpackage %s/%s"%(domain,name))
        services[0]=services[0].newInstance(instance, args=args, hrddata=hrddata)
        return services[0]

    def get(self,domain="",name="",instance="main"):
        self._doinit()
        services=self.find(domain,name,1)
        if len(services)==0:
            j.events.opserror_critical("cannot find jpackage %s/%s"%(domain,name))
        services[0]=services[0].getInstance(instance, args=args, hrddata=hrddata)
        return services[0]


    def exists(self,domain="",name="",instance="main",node=""):
        self._doinit()
        services=self.find(domain,name,1)
        if len(services)==0:
            return False
        return  services[0].existsInstance(instance=instance,node=node)

    def __str__(self):
        return self.__repr__()
