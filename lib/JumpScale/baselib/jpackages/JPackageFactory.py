from JumpScale import j
from .JPackage import JPackage

from .ActionsBase import ActionsBase

class JPackageFactory():

    def __init__(self):
        self._init=False
        self.domains={}
        self.hrd=None

    def _doinit(self):
        if self._init==False:
            j.do.debug=False
            login=j.application.config.get("whoami.git.login").strip()
            passwd=j.application.config.get("whoami.git.passwd").strip()
            items=j.application.config.getDictFromPrefix("jpackage.metadata")
            repos=j.do.getGitReposListLocal()            
            for domain in items.keys():                
                url=items[domain]
                domain=domain.rpartition(".url")[0]
                reponame=url.rpartition("/")[-1]
                if not reponame in repos.keys():
                    #means git has not been pulled yet
                    if login!="":
                        dest=j.do.pullGitRepo(url,dest=None,login=login,passwd=passwd,depth=1,ignorelocalchanges=False,reset=False,branch="master")
                    else:
                        dest=j.do.pullGitRepo(url,dest=None,depth=1,ignorelocalchanges=False,reset=False,branch="master")
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

        res=[]
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

        #now name & domain is known
        if maxnr!=None and len(res)>maxnr:
            j.events.inputerror_critical("Found more than %s jpackage for query '%s':'%s'"%(maxnr,domain,name))    

        return res    

    def get(self,domain="",name=""):
        self._doinit()
        jps=self.find(domain,name,1)
        if len(jps)==0:
            j.events.opserror_critical("cannot find jpackage %s/%s"%(domain,name))
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
            source="%s/apps/"%j.dirs.hrdDir
            self.hrd=j.core.hrd.get(source)
        
        return self.hrd

    def __str__(self):
        return self.__repr__()