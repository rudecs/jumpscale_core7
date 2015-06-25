import os

try:
    import ujson as json
except:
    import json
    
from JumpScale import j
from JumpScale.core.baseclasses import BaseEnumeration
from .WhmcsInstance import WhmcsInstance

class Dummy(object):
    def __getattribute__(self, attr, *args, **kwargs):
        def dummyFunction(*args, **kwargs):
            pass
        return dummyFunction
    def __setattribute__(self, attr, val):
        pass

class DummyWhmcs(object):
    def __init__(self):
        self.tickets = Dummy()
        self.orders = Dummy()
        self.users = Dummy()

class WhmcsFactory(object):

    def __init__(self):
        j.logger.consolelogCategories.append('whmcs')

    def get(self,
            username='',
            md5_password='',
            accesskey='',
            url='',
            cloudspace_product_id='',
            operations_user_id='',
            operations_department_id='',
            instance='main'):

        return WhmcsInstance(username,
            md5_password,
            accesskey,
            url,
            cloudspace_product_id,
            operations_user_id,
            operations_department_id,
            instance)
        
    
    def getDummy(self):
        return DummyWhmcs()

    def log(self,msg,category='',level=5):
        category = 'whmcs.%s'%category
        category = category.rstrip('.')
        j.logger.log(msg,category=category,level=level)