try:
    import ujson as json
except:
    import json
    
from JumpScale import j

import os

import gitlab3
import JumpScale.baselib.git

class GitlabInstance():

    def __init__(self,addr="",login="",passwd="",instance="main"):

        if addr=="":
            hrd=j.application.getAppInstanceHRD("gitlab_client",instance)
            self.addr=hrd.get("gitlab.client.url")
            self.login=hrd.get("gitlab.client.login")
            self.passwd=hrd.get("gitlab.client.passwd")            
        else:
            self.addr=addr
            self.login=login
            self.passwd=passwd

        self.gitlab=gitlab3.GitLab(self.addr)
        self.gitlab.login(self.login, password=self.passwd)

    # def getGitClient(self, accountName, repoName="", branch="master", clean=False,path=None):
    #     """
    #     @param path if not is std codefolder (best practice to leave this default)
    #     """
    #     repoName=repoName.replace(".","-")
    #     #if self.gitclients.has_key(repoName):
    #         #return self.gitclients[repoName]
    #     #@todo P2 cache the connections but also use branchnames
    #     self.accountName = accountName
    #     if repoName=="":
    #         repoName=self.findRepoFromGitlab(repoName)
    #     if repoName=="":
    #         raise RuntimeError("reponame cannot be empty")

    #     # if self.passwd=="":
    #     url = 'git@%s:' % (self.addr)
    #     # else:
    #     #     url = 'http://%s:%s@%s' % (self.loginName,self.passwd,self.addr)
    #     #     # url = 'http://%s' % (self.addr)
    #     #     if url[-1] != "/":
    #     #         url=url+"/"

    #     url += "%s/%s.git" % (accountName, repoName)

    #     j.clients.gitlab.log("init git client ##%s## on path:%s"%(repoName,self.getCodeFolder(repoName)),category="getclient")
    #     if path==None:
    #         path=self.getCodeFolder(repoName)

    #     try:
    #         cl = j.clients.git.getClient(path, url, branchname=branch, cleandir=clean,login=self.loginName,passwd=self.passwd)
    #     except Exception as e:
    #         if not j.system.fs.exists(path=path):
    #             #init repo


    #             cl = j.clients.git.getClient(path, url, branchname=branch, cleandir=clean,login=self.loginName,passwd=self.passwd)

        
    #     # j.clients.gitlab.log("git client inited for repo:%s"%repoName,category="getclient")
    #     self.gitclients[repoName]=cl
    #     return cl

    # def getCodeFolder(self, repoName):
    #     return j.system.fs.joinPaths(j.dirs.codeDir, "git_%s" % self.accountName, repoName)

    def getGroup(self,name,die=True):
        groups=self.gitlab.groups()
        for group in groups:
            if group.name.lower()==name:
                return group
        if die:
            j.events.inputerror_critical("Cannot find group with name:%s"%name)
        else:
            return None

    def getProject(self,name,die=True):
        items=self.gitlab.projects()
        for item in items:
            if item.name.lower()==name:
                return item
        if die:
            j.events.inputerror_critical("Cannot find project with name:%s"%name)
        else:
            return None


    def create(self,group,name,public=False):
        group2=self.getGroup(group)
        ttype=self.addr.split("/",1)[1].strip("/ ")
        if ttype.find(".")!=-1:
            ttype=ttype.split(".",1)[0]
        path="%s/%s/%s/%s"%(j.dirs.codeDir,ttype,group,name)        
        if self.getProject(name,False)==None:
            self.gitlab.add_project(name,public=public,namespace_id=group2.id)
            proj=self.getProject(name)
            j.do.delete(path, force=True)
            j.system.fs.createDir(path)
            def do(cmd):
                j.system.process.executeWithoutPipe("cd %s;%s"%(path,cmd))    
            do("git init")                
            do("touch README")
            do("git add README")
            do("git commit -m 'first commit'")
            addr=self.addr.split("/",1)[1].strip("/ ")
            do("git remote add origin https://%s:%s@%s/%s/%s.git"%(self.login,self.passwd,addr,group,name))
            do("git push -u origin master")  
        else:          
            proj=self.getProject(name)
            url=proj.web_url
            j.do.pullGitRepo(url=url, dest=None, login=self.login, passwd=self.passwd, depth=1, ignorelocalchanges=False, reset=False, branch=None, revision=None)
            
        return proj,path
