import os

try:
    import ujson as json
except:
    import json
    
from JumpScale import j
from JumpScale.core.baseclasses import BaseEnumeration
from .OauthInstance import *

class OauthFactory(object):

    def __init__(self):
        j.logger.consolelogCategories.append('oauth')

    def get(self, addr='', accesstokenaddr='', id='', secret='', scope='', redirect_url='', user_info_url='', instance='github'):        
        return OauthInstance(addr, accesstokenaddr, id, secret, scope, redirect_url, user_info_url, instance)

    def log(self,msg,category='',level=5):
        category = 'oauth.%s'%category
        category = category.rstrip('.')
        j.logger.log(msg,category=category,level=level)