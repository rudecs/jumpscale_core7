try:
    import ujson as json
except:
    import json
from JumpScale import j

from .whmcsusers import whmcsusers
from .whmcstickets import whmcstickets
from .whmcsorders import whmcsorders

class WhmcsInstance(object):
    def __init__(self,
                 username,
                 md5_password,
                 accesskey,
                 url,
                 cloudspace_product_id,
                 operations_user_id,
                 operations_department_id,
                 instance):

        if not username:
            hrd = j.application.getAppInstanceHRD('whmcs_client', instance)
            self._username = hrd.get('instance.whmcs.client.username')
            self._md5_password = hrd.get('instance.whmcs.client.md5_password')
            self._accesskey = hrd.get('instance.whmcs.client.accesskey')
            self._url = hrd.get('instance.whmcs.client.url')
            self._cloudspace_product_id = hrd.get('instance.whmcs.client.cloudspace_product_id')
            self._operations_user_id = hrd.get('instance.whmcs.client.operations_user_id')
            self._operations_department_id = hrd.get('instance.whmcs.client.operations_department_id')
        else:
            self._username = username
            self._md5_password = md5_password
            self._accesskey = accesskey
            self._url = url
            self._cloudspace_product_id = cloudspace_product_id
            self._operations_user_id = operations_user_id
            self._operations_department_id = operations_department_id
        
        self._whmcsusers = None
        self._whmcstickets = None
        self._whmcsorders = None

    @property
    def users(self):
        authenticationparams = {
            'username' : self._username,
            'password' : self._md5_password,
            'accesskey' : self._accesskey}
        
        if not self._whmcsusers:
            self._whmcsusers = whmcsusers(authenticationparams, self._url)
        return self._whmcsusers

    @property
    def tickets(self):
        authenticationparams = {
            'username' : self._username,
            'password' : self._md5_password,
            'accesskey' : self._accesskey}
        
        if not self._whmcstickets:
            self._whmcstickets = whmcstickets(authenticationparams,
                                             self._url,
                                             self._operations_user_id,
                                             self._operations_department_id)
        return self._whmcstickets
    
    @property
    def orders(self):
        authenticationparams = {
            'username' : self._username,
            'password' : self._md5_password,
            'accesskey' : self._accesskey}
        
        if not self._whmcsorders:
            self._whmcsorders = whmcsorders(authenticationparams, self._url)
        return self._whmcsorders