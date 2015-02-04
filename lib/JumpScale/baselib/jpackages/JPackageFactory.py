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

    def _doinit(self):

        if self._init==False:
            j.do.debug=False

            if j.system.fs.exists(path="/etc/my_init.d"):
                self.indocker=True

            login=j.application.config.get("whoami.git.login").strip()
            passwd=j.application.config.getStr("whoami.git.passwd").strip()

            if self.type != "n":
                configpath=j.dirs.amInGitConfigRepo()
                self.domains[j.system.fs.getBaseName(configpath)]="%s/jp/"%configpath

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

    def find(self,domain="",name="",maxnr=None):
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

        res = {}
        items=j.application.config.getDictFromPrefix("jpackage.metadata")
        for domainfound in sorted(self.domains.keys(), cmp=sorter):
            for namefound in j.system.fs.listDirsInDir(path=self.domains[domainfound], recursive=False, dirNameOnly=True, findDirectorySymlinks=False):
                if namefound in [".git"]:
                    continue
                if domain=="" and name=="":
                    if namefound not in res:
                        res[namefound] = domainfound
                elif domain=="" and name!="":
                    if name==namefound:
                        if namefound not in res:
                            res[namefound] = domainfound
                elif domain!="" and name=="":
                    if domain==domainfound:
                        if namefound not in res:
                            res[namefound] = domainfound
                else:
                    if domain==domainfound and name==namefound:
                        if namefound not in res:
                            res[namefound] = domainfound

        finalRes=[]
        for name,domain in res.iteritems():
            finalRes.append(JPackage(domain,name))
        #now name & domain is known
        if maxnr!=None and len(finalRes)>maxnr:
            j.events.inputerror_critical("Found more than %s jpackage for query '%s':'%s'"%(maxnr,domain,name))

        return finalRes

    def get(self,domain="",name="",instance="main",args={}, hrddata=None,node=""):
        self._doinit()
        jps=self.find(domain,name,1)
        if len(jps)==0:
            j.events.opserror_critical("cannot find jpackage %s/%s"%(domain,name))
        jps[0]=jps[0].getInstance(instance, args=args, hrddata=hrddata,node=node)
        return jps[0]

    def exists(self,domain="",name="",instance="main",node=""):
        self._doinit()
        jps=self.find(domain,name,1)
        if len(jps)==0:
            return False
        return  jps[0].existsInstance(instance=instance,node=node)

    # def install(self,domain="",name="",instance="main",args={}, hrddata=None):
    #     self._doinit()
    #     jp=self.get(domain,name)
    #     if instance=="":
    #         j.events.inputerror_critical("instance cannot be empty when installing a jpackage","jpackage.install")
    #     jpi=jp.getInstance(instance, args=args, hrddata=hrddata)
    #     return jpi.install()

    # def getHRD(self,reload=True):
    #     if self.hrd==None or reload:
    #         if self.type=="n":
    #             source="%s/apps/"%self.domains[0]
    #         else:
    #             source="%s/apps/"%j.dirs.hrdDir
    #         self.hrd=j.core.hrd.get(source)

    #     return self.hrd

    def __str__(self):
        return self.__repr__()
