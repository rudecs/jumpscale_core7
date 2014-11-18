try:
    import ujson as json
except:
    import json
    
from JumpScale import j
from JumpScale.core.baseclasses import BaseEnumeration

# import urllib
# import requests
# from requests.auth import HTTPBasicAuth
from . import gitlab
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

    def get(self,account):        
        return GitlabInstance(account)

    def log(self,msg,category="",level=5):
        category="gitlab.%s"%category
        category=category.rstrip(".")
        j.logger.log(msg,category=category,level=level)
