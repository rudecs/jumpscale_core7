from GitClient import GitClient
from JumpScale import j


class GitFactory:
    def __init__(self):
        j.logger.consolelogCategories.append("git")

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
