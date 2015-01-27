from .GitClient import GitClient
from JumpScale import j


class GitFactory:
    def __init__(self):
        j.logger.consolelogCategories.append("git")

    def getClientFromUrl(self,url="",dest=None,login=None,passwd=None,depth=1,ignorelocalchanges=False,reset=False,branch=None,revision=None):
        
        base,ttype,account,repo,dest,url=j.do.getGitRepoArgs(url,dest,login,passwd,reset=reset)

        if login==None:
            from IPython import embed
            print "DEBUG NOW ooo1"
            embed()
            
                
            if j.application.config.get("whoami.git.login",default="")!="":
                login=j.application.config.get("whoami.git.login")
                passwd=j.application.config.get("whoami.git.passwd")


    def getClient(self, basedir, remoteUrl="", branchname='master', cleandir=False,login=None,passwd=None):
        """
        return a mercurial tool which you can help to manipulate a hg repository
        @param base dir where local gitrepository will be stored
        @param remote url of git repository, e.g. https://login:passwd@bitbucket.org/despiegk/ssospecs/  #DO NOT FORGET LOGIN PASSWD
        """
        if not isinstance(cleandir, bool):
            raise ValueError("cleandir needs to be boolean")
        return GitClient(basedir, remoteUrl, branchname, cleandir,login=login,passwd=passwd)

    def log(self,msg,category="",level=5):
        category="git.%s"%category
        category=category.rstrip(".")
        j.logger.log(msg,category=category,level=level)
