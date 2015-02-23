import datetime
try:
    import ujson as json
except:
    import json
    
from JumpScale import j

import os

import gitlab3
import JumpScale.baselib.git

def lazyLogIn(function):
    """
    Gitlab client REST API are very slow, directly authenticating portal against gitlab
    take time and shouldn't be done at the very beginning of starting portal.
    This docorator makes sure that whenever a gitlab client function is called
    the client will be authenticated if not already.
    """
    def wrapper(self, *args, **kwargs):
        if not self.isLoggedIn:
            login = self.login
            passwd = self.passwd
            self.isLoggedIn = self.authenticate(login, passwd)
        return function(self, *args, **kwargs)
    return wrapper

class GitlabInstance():
    """
    Wrapper around gitlab3 library with Caching capabilities to improve performance.
    """

    # GITLAB permissions as keys mapped to jumpscale permissions scheme 
    PERMISSIONS = {
        10:'',    #guest
        20:'r',   #reporter
        30:'rw',  #developer
        40:'rwa', #master
        50:'rwa'  #owner
    }
    
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
        self.isLoggedIn = False
        self._cache = {}
        self._cache_lifetime_seconds = 360

    def _getFromCache(self, username, key):
        """
        Since gitlab client is way to slow, we need to cache results
        for performance sake.
        This function returns the result if not lifetime exceeded 5 minutes
        otherwise returns null.
        
        """
        now = datetime.datetime.now()
        user_cache = self._cache.get(username)
        res = {'expired':True, 'data':None}
        if user_cache:
            cache = user_cache.get(key)
            if cache:
                timestamp = cache.get('timestamp')
                if (now - timestamp).seconds < self._cache_lifetime_seconds:
                    res['data'] = cache.get('value')
                    res['expired'] = False
                else:
                    res['expired'] = True
        return res
                
    def _addToCache(self, username, key, value):
        """
        Since gitlab client is way to slow, we need to cache results
        for performance sake.
        This function used to add key/value to cache
        
        Cache data model:
        
        {'faragh':{'userspaces':'value':['portal_one', 'portal_two'], 'timestamp':datetime.datetime(2015, 2, 22, 14, 13, 24, 332260)}}
        
        """
        now = datetime.datetime.now()
        if not username in self._cache:
            self._cache[username] = {}
        if not key in self._cache[username]:
            self._cache[username][key] = {}
        self._cache[username][key]['value'] = value
        self._cache[username][key]['timestamp'] = now

    def authenticate(self, login, password):
        """
        Everytime a user authenticates, he has a new client instance
        To overcome Race conditions
        """
    
        new_client = gitlab3.GitLab(self.addr)
        self.isLoggedIn = True
        return new_client.login(login, password)

    @lazyLogIn
    def getGroupInfo(self, groupname, force_cache_renew=False, die=True):
        """
        Get a group info 
        
        @param groupname: groupname
        @type groupname: ``str``
        @param force_cache_renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
        @type force_cache_renew: ``boolean`` 
        @param die: Raise exception if group not found
        @type die: ``boolean`` 
        @return: ``` gitlab3.Group ```
        
        """
        key = ('group', groupname)
        if not force_cache_renew:
            result = self._getFromCache(self.login, key)
            if not result['expired']:
                return result['data']
        
        group = self.gitlab.find_group(name=groupname)
        self._addToCache(self.login, key, group)
        
        if group:
            return group
        if die:
            j.events.inputerror_critical("Cannot find group with name:%s"%groupname)
        else:
            return None
    
    @lazyLogIn
    def getSpace(self, name, force_cache_renew=False, die=False):
        """
        Get Space Info [Space is a project]
        
        @param name: Project/Space name
        @type name: ``str``
        @param force_cache_renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
        @type force_cache_renew: ``boolean`` 
        @param die: Raise exception if space not found
        @type die: ``boolean``
        @return: ```gitlab3.Project```
        """
        key = ('project', name)
        if not force_cache_renew:
            result = self._getFromCache(self.login, key)
            if not result['expired']:
                return result['data']
        
        p = self.gitlab.find_project(name=name)
        self._addToCache(self.login, key, p)
        if p:
            return p
        if die:
            j.events.inputerror_critical("Cannot find project with name:%s"%name)
    
    @lazyLogIn
    def create(self,group, name, public=False):
        """
        Create a space/project in a certain group
        
        @param group: groupname
        @type group: ``str``
        @param name: space name
        @type name: ``str``
        """
        group2=self.getGroupInfo(group, force_cache_renew=True)
        ttype=self.addr.split("/",1)[1].strip("/ ")
        if ttype.find(".")!=-1:
            ttype=ttype.split(".",1)[0]
        path="%s/%s/%s/%s"%(j.dirs.codeDir,ttype,group,name)        
        if not self.getSpace(name, force_cache_renew=True, die=False):
            self.gitlab.add_project(name,public=public,namespace_id=group2.id)
            proj=self.getSpace(name, force_cache_renew=True)
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
            proj=self.getSpace(name, force_cache_renew=True)
            url=proj.web_url
            if group:
                return group
            j.do.pullGitRepo(url=url, dest=None, login=self.login, passwd=self.passwd, depth=1, ignorelocalchanges=False, reset=False, branch=None, revision=None)
            
        return proj,path

    @lazyLogIn
    def getUserInfo(self, username, force_cache_renew=False):
        """
        Returns user info
        
        @param username: username
        @type username: ``str``
        @return: ```gitlab3.User``` 
        """
        key = ('user', username)
        
        if not force_cache_renew:
            result = self._getFromCache(self.login, key)
            if not result['expired']:
                return result['data']
        u = self.gitlab.find_user(username=username)
        self._addToCache(self.login, key, u)
        return u

    @lazyLogIn
    def userExists(self, username, force_cache_renew=False):
        """
        Check user exists
        
        @param username: username
        @type username: ``str``
        @return: ``bool`` 
        """
        return bool(self.getUserInfo(username, force_cache_renew))

    @lazyLogIn
    def createUser(self, username, password, email, groups):
        id = self.gitlab.add_user(username=username, password=password, email=email)
        for group in groups:
            g = self.gitlabclient.find_group(name=group)
            g.add_member(id)
            g.save()
        
        self.listUsers(force_cache_renew=True)
        
    @lazyLogIn
    def listUsers(self, force_cache_renew=False):
        """
        Get All users
        @param force_cache_renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
        @type force_cache_renew: ``boolean`` 
        @return: ``lis``
        """
        if not force_cache_renew:
            result = self._getFromCache(self.login, 'users')
            if not result['expired']:
                return result['data']
        users =  self.gitlab.users()
        self._addToCache(self.login, 'users', users)
        return users

    @lazyLogIn
    def listGroups(self, force_cache_renew=False):
        """
        GET ALL groups in gitlab that admin user (self.login) has access to
        
        @param force_cache_renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
        @type force_cache_renew: ``boolean`` 
        @return: ``lis``
        """
        if not force_cache_renew:
            result =  self._getFromCache(self.login, 'groups')
            if not result['expired']:
                return result['data']
        all_groups = self.gitlab.groups()
        self._addToCache(self.login, 'groups', all_groups)
        return all_groups
    
    @lazyLogIn
    def getGroups(self,username, force_cache_renew=False):
        """
        Get groups for a certain user
        
        @param username: username
        @type username: ``str``
        @param force_cache_renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
        @type force_cache_renew: ``boolean`` 
        @return: ``lis``
        """

        if not force_cache_renew:
            result = self._getFromCache(username, 'groups')
            if not result['expired']:
                return result['data']
        try:
            groups =  [ group.name for group in self.gitlab.groups(sudo=username) ]
            self._addToCache(username, 'groups', groups)
            return groups
        except gitlab3.exceptions.ForbiddenRequest:
            self._addToCache(username, 'groups', [])
            return []
    
    @lazyLogIn
    def getUserSpaceRights(self, username, space, **kwargs):
        """
        
        10:'', #guest
        20:'r', #reporter
        30:'rw', #developer
        40:'*', #master
        50:'*'  #owner

        @param space: user space (Project) in gitlab
        @type space: ```gitlab3.Project```
        """
        space = self.getSpace(space)
        if not space:
            raise RuntimeError("Space %s not found" % space)
        rights = space.find_member(username=username)
        if rights:
            return username, self.PERMISSIONS[rights.access_level]
        return username, ''
    
    @lazyLogIn
    def getUserSpaces(self, username, force_cache_renew=False):
        """
        Get userspace names for a specific user
        Gitlab userspaces always start with 'portal_'
        
        @param username: username
        @type username: `str`
        @param bypass_cache: If True, Force getting data from gitlab backend, otherwise try to get it from cache 1st 
        @type bypass_cache:`bool` 
        """
        if not force_cache_renew:
            result =  self._getFromCache(username, 'spaces')
            if not result['expired']:
                return result['data']

        try:
            userspaces =  [p.name for p in self.gitlab.find_projects_by_name('portal_', sudo=username)]
            self._addToCache(username, 'spaces', userspaces)
            return userspaces
        except gitlab3.exceptions.ForbiddenRequest:
            self._addToCache(username, 'spaces', [])
            return []