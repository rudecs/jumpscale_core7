try:
    import ujson as json
except:
    import json
    
from JumpScale import j

import os

import gitlab
import JumpScale.baselib.git

class GitlabInstance():

    def __init__(self,addr="",login="",passwd="",instance="main"):

        if addr=="":
            hrd=j.application.getAppInstanceHRD("gitlab_client",instance)
            self.addr=hrd.get("gitlab.addr")
            self.login=hrd.get("gitlab.login")
            self.passwd=hrd.get("gitlab.passwd")            
        else:
            self.addr=addr
            self.login=login
            self.passwd=passwd

        self.gitlab=gitlab.Gitlab(host=self.addr)
        self.gitlab.login(user=self.login, password=self.passwd)



    def getGitClient(self, accountName, repoName="", branch="master", clean=False,path=None):
        """
        @param path if not is std codefolder (best practice to leave this default)
        """
        repoName=repoName.replace(".","-")
        #if self.gitclients.has_key(repoName):
            #return self.gitclients[repoName]
        #@todo P2 cache the connections but also use branchnames
        self.accountName = accountName
        if repoName=="":
            repoName=self.findRepoFromGitlab(repoName)
        if repoName=="":
            raise RuntimeError("reponame cannot be empty")

        # if self.passwd=="":
        url = 'git@%s:' % (self.addr)
        # else:
        #     url = 'http://%s:%s@%s' % (self.loginName,self.passwd,self.addr)
        #     # url = 'http://%s' % (self.addr)
        #     if url[-1] != "/":
        #         url=url+"/"

        url += "%s/%s.git" % (accountName, repoName)

        j.clients.gitlab.log("init git client ##%s## on path:%s"%(repoName,self.getCodeFolder(repoName)),category="getclient")
        if path==None:
            path=self.getCodeFolder(repoName)

        try:
            cl = j.clients.git.getClient(path, url, branchname=branch, cleandir=clean,login=self.loginName,passwd=self.passwd)
        except Exception as e:
            if not j.system.fs.exists(path=path):
                #init repo
                j.system.fs.createDir(path)
                def do(cmd):
                    j.system.process.executeWithoutPipe("cd %s;%s"%(path,cmd))    
                do("git init")                
                do("touch README")
                do("git add README")
                do("git commit -m 'first commit'")
                raise RuntimeError("change, need to use specific repo names")
                do("git remote add origin git@gitlab.a.incubaid.com:lenoir1/backup_lxc_ubuntu_13-10_base.git")
                do("git push -u origin master")

                cl = j.clients.git.getClient(path, url, branchname=branch, cleandir=clean,login=self.loginName,passwd=self.passwd)

        
        # j.clients.gitlab.log("git client inited for repo:%s"%repoName,category="getclient")
        self.gitclients[repoName]=cl
        return cl

    def getCodeFolder(self, repoName):
        return j.system.fs.joinPaths(j.dirs.codeDir, "git_%s" % self.accountName, repoName)

