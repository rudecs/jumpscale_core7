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
        self.authenticate(login, passwd)

    def authenticate(self, login, password):
        """
        Everytime a user authenticates, he has a new client instance
        To overcome Race conditions
        """
        new_client = gitlab3.GitLab(self.addr)
        return new_client.login(login, password)

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

    def getUserInfo(self, username):
        return self.gitlab.find_user(username=username)

    def getGroupInfo(self, groupname):
        return self.gitlab.getGroup(groupname)

    def userExists(self, username):
        return bool(self.getUserInfo(username))

    def createUser(self, username, password, email, groups=['binary']):
        id = self.gitlab.add_user(username=username, password=password, email=email)
        for group in groups:
            g = self.gitlabclient.find_group(name=group)
            g.add_member(id)
            g.save()

    def listUsers(self):
        return self.gitlab.users()

    def listGroups(self):
        return self.gitlab.groups()

    def getGroups(self,username):
        result = []
        for group in self.gitlab.groups():
            for member in  group.members():
                if member.username == username:
                    result.append(group.name)
        return result
