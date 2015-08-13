try:
    import ujson as json
except:
    import json
    
from JumpScale import j
from JumpScale.core.baseclasses import BaseEnumeration

# import urllib
# import requests
# from requests.auth import HTTPBasicAuth
# from . import gitlab
import os

from .GitlabInstance import *

# INFOCACHE = dict()

class GitlabFactory:
    """
    Gitlab client enables administrators and developers leveraging Gitlab services through JumpScale
    """

    def __init__(self):
        self.connections={}
        j.logger.consolelogCategories.append("gitlab")

    def get(self,gitlaburl="",login="",passwd="",instance="main"):        
        """
        example for gitlaburl
            https://despiegk:dddd@git.aydo.com
        can also be without login:passwd
            e.g. https://git.aydo.com and specify login/passwd

        if gitlaburl is empty then 
            hrd is used as follows:
            hrd=j.application.getAppInstanceHRD("gitlab_client",instance)
            gitlaburl=hrd.get("gitlab.client.url")
            login=hrd.get("gitlab.client.login")
            passwd=hrd.get("gitlab.client.passwd")

        """
        if login =="":
            if not gitlaburl.find("@"):
                j.events.inputerror_critical("login not specified, expect an @ in url")
            data=gitlaburl.split("@")[0]
            if data.find("http")==0:
                data=data.split("//")[1]
            login,passwd=data.split(":")
            gitlaburl=gitlaburl.replace("%s:%s@"%(login,passwd),"")

        return GitlabInstance(addr=gitlaburl,login=login,passwd=passwd,instance=instance)

    def log(self,msg,category="",level=5):
        category="gitlab.%s"%category
        category=category.rstrip(".")
        j.logger.log(msg,category=category,level=level)

    def getAccountnameReponameFromUrl(self,url):
        repository_host, repository_type, repository_account, repository_name, repository_url= j.do.rewriteGitRepoUrl( url)
        repository_name=repository_name.replace(".git","")
        return (repository_account, repository_name)
