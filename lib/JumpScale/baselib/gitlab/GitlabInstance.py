try:
    import ujson as json
except:
    import json
    
from JumpScale import j
from JumpScale.core.baseclasses import BaseEnumeration

# from GitlabConfigManagement import *
# import urllib
# import requests
# from requests.auth import HTTPBasicAuth
import gitlab
import os

from gitlab import Gitlab
import JumpScale.baselib.git

class GitlabInstance(Gitlab):

    def __init__(self,account ):

        id=0
        for key in j.application.config.getKeysFromPrefix("gitlabclient.server"):
            # key=key.replace("gitlabclient.server.","")
            if key.find("name")<>-1:
                if j.application.config.get(key)==account:
                    key2=key.replace("gitlabclient.server.","")
                    id=key2.split(".")[0]
        if id==0:
            raise RuntimeError("Did not find account:%s for gitlab"%account)
        prefix="gitlabclient.server.%s"%id
        self.addr=j.application.config.get("%s.addr"%prefix)

        # self.accountPathLocal = j.system.fs.joinPaths("/opt/code",accountName)
        # j.system.fs.createDir(self.accountPathLocal)
        # self._gitlab = gitlab.Gitlab(self.addr)
        login=j.application.config.get("%s.login"%prefix)
        passwd=j.application.config.get("%s.passwd"%prefix)
        self.passwd=passwd
        if passwd<>"":
            
            Gitlab.__init__(self, self.addr)#, token=token)
            self.login(login, passwd)
            self.load()
        # for item in dir(self._gitlab):
        #     if item[0]<>"_":
        #         setattr(self,item,getattr(self._gitlab,item))
        self.gitclients={}
            
        self.loginName=login
        self.port=80

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
        #     if url[-1]<>"/":
        #         url=url+"/"

        url += "%s/%s.git" % (accountName, repoName)

        j.clients.gitlab.log("init git client ##%s## on path:%s"%(repoName,self.getCodeFolder(repoName)),category="getclient")
        if path==None:
            path=self.getCodeFolder(repoName)

        try:
            cl = j.clients.git.getClient(path, url, branchname=branch, cleandir=clean,login=self.loginName,passwd=self.passwd)
        except Exception,e:
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

