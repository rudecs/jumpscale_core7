from JumpScale import j
from .JPackage import JPackage

from .ActionsBase import ActionsBase

class JPackageFactory():

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

    def _doinit(self, remote=False):
        if self._init==False:
            j.do.debug=False

            if j.system.fs.exists(path="/etc/my_init.d"):
                self.indocker=True

            login=j.application.config.get("whoami.git.login").strip()
            passwd=j.application.config.getStr("whoami.git.passwd").strip()
            if self.type == "n":
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
                    dest=repos[reponame]
                    self.domains[domain]=dest
            else:
                configpath=j.dirs.amInGitConfigRepo()
                self.domains[j.system.fs.getBaseName(configpath)]="%s/jp/"%configpath

            self_init=True

    def getActionsBaseClass(self):
        return ActionsBase

    def getDomains(self):
        return self.domains.keys()

    def find(self,domain="",name="",maxnr=None,remote=False):
        self._doinit(remote=remote)

        #create some shortcuts for fast return
        if domain!="":
            if domain not in self.domains:
                return[]
            if name!="":
                if not j.system.fs.exists(path="%s/%s"%(self.domains[domain],name)):
                    return []

        res=[]
        if not remote:
            for domainfound in self.domains.keys():
                for namefound in j.system.fs.listDirsInDir(path=self.domains[domainfound], recursive=False, dirNameOnly=True, findDirectorySymlinks=False):
                    if namefound in [".git"]:
                        continue
                    if domain=="" and name=="":
                        res.append(JPackage(domainfound,namefound))
                    elif domain=="" and name!="":
                        if name==namefound:
                            res.append(JPackage(domainfound,namefound))
                    elif domain!="" and name=="":
                        if domain==domainfound:
                            res.append(JPackage(domainfound,namefound))
                    else:
                        if domain==domainfound and name==namefound:
                            res.append(JPackage(domainfound,namefound))
        else: #remote execution
            # for domainfound in self.domains.keys():
            # from ipdb import set_trace;set_trace()
            actionsPath = j.dirs.getJPActionsPath()
            setPkg = set()
            for namefound in j.system.fs.listFilesInDir(path=actionsPath):
                split = j.system.fs.getBaseName(namefound).split("__")
                domainfound = split[0]
                namefound = split[1]
                if namefound in [".git"]:
                    continue
                if domain=="" and name=="":
                    # res.append(JPackage(domainfound,namefound))
                    setPkg.add("%-15s:%s"%(domainfound,namefound))
                elif domain=="" and name!="":
                    if name==namefound:
                        setPkg.add("%-15s:%s"%(domainfound,namefound))
                        # res.append(JPackage(domainfound,namefound))
                elif domain!="" and name=="":
                    if domain==domainfound:
                        setPkg.add("%-15s:%s"%(domainfound,namefound))
                        # res.append(JPackage(domainfound,namefound))
                else:
                    if domain==domainfound and name==namefound:
                        setPkg.add("%-15s:%s"%(domainfound,namefound))
                        # res.append(JPackage(domainfound,namefound))
            for pkg in setPkg:
                domain,name = (pkg.split(':'))
                res.append(JPackage(domain.strip(),name.strip(),remote=True))
        #now name & domain is known
        if maxnr!=None and len(res)>maxnr:
            j.events.inputerror_critical("Found more than %s jpackage for query '%s':'%s'"%(maxnr,domain,name))

        return res

    def get(self,domain="",name="",instance="",args={}):
        self._doinit()
        jps=self.find(domain,name,1)
        if len(jps)==0:
            j.events.opserror_critical("cannot find jpackage %s/%s"%(domain,name))
        if instance!="":
            jps[0]=jps[0].getInstance(instance)
            jps[0].args=args
        return jps[0]

    def install(self,domain="",name="",instance="main",args={}):
        self._doinit()
        jp=self.get(domain,name)
        if instance=="":
            j.events.inputerror_critical("instance cannot be empty when installing a jpackage","jpackage.install")
        jpi=jp.getInstance(instance)
        return jpi.install(args=args)

    def getHRD(self,reload=True):
        if self.hrd==None or reload:
            if self.type=="n":
                source="%s/apps/"%self.domains[0]
            else:
                source="%s/apps/"%j.dirs.hrdDir
            self.hrd=j.core.hrd.get(source)

        return self.hrd

    def __str__(self):
        return self.__repr__()
