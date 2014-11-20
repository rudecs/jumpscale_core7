from JumpScale import j

class JPackageFactory():

    def __init__(self):
        self._init=False

    def _doinit(self):
        if self._init==False:
            login=j.application.config.get("whoami.git.login").strip()
            passwd=j.application.config.get("whoami.git.passwd").strip()
            items=j.application.config.getDictFromPrefix("jpackage.metadata")
            for domain in items.keys():
                url=items[domain]
                domain=domain.rpartition(".url")[0]
                if not url.rpartition("/")[-1] in j.do.getGitReposListLocal().keys():
                    #means git has not been pulled yet
                    if login!="":
                        j.do.pullGitRepo(url,dest=None,login=login,passwd=passwd,depth=1,ignorelocalchanges=False,reset=False,branch="master")
                    else:
                        j.do.pullGitRepo(url,dest=None,depth=1,ignorelocalchanges=False,reset=False,branch="master")
            self_init=True

    def getdomains(self):
        items=j.application.config.getDictFromPrefix("jpackage.metadata")
        res=[]
        for domain in items.keys():
            domain=domain.rpartition(".url")[0]
            res.append(domain.strip())
        return res

    def find(self,domain="",name="",instance="",maxnr=None):
        self._doinit()
        from IPython import embed
        print(10)
        embed()
        

    def get(self,domain="",name="",instance=""):
        self._doinit()
        jp=self.find(domain,name,instance,1)
        return jp
        
    def install(self,domain="",name="",instance="",args={}):
        self._doinit()
        jp=self.get(domain,name,instance)
        jp.install()

    def __str__(self):
        return self.__repr__()

