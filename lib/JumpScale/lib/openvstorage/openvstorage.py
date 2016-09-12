import requests
import os
from requests.auth import HTTPBasicAuth


class OpenvStorageFactory(object):
    def get(self, ip, credentials, verify=False):
        """
        Gets dynamic client for OpenvStorageClient

        Example:
        client = OpenvStorageClient(ip, credentials)
        client.login()
        client.vdisks() # get requests
        taskguid = client.vdisks(method='post', json={}) # post requests
        task = client.tasks[taskguid]()
        vdiskguid = task['result']
        client.vdisks['<vdisguid']() # get details of disk
        """
        return OpenvStorageClient(ip, credentials, verify)


class ApiError(Exception):
    def __init__(self, response):
        super(ApiError, self).__init__('%s %s' % (response.status_code, response.reason))
        self._response = response

    @property
    def response(self):
        return self._response


class BaseResource(object):
    def __init__(self, session, url):
        self._session = session
        self._url = url

    def __getattr__(self, item):
        url = os.path.join(self._url, item)
        resource = BaseResource(self._session, url)
        setattr(self, item, resource)
        return resource

    def __getitem__(self, item):
        url = os.path.join(self._url, item)
        resource = BaseResource(self._session, url)
        return resource

    def __call__(self, method='get', **kwargs):
        func = getattr(self._session, method)
        url = self._url
        if method == 'post':
            url += '/'
        response = func(url, **kwargs)

        if not response.ok:
            raise ApiError(response)

        if response.headers.get('content-type', 'text/html').startswith('application/json'):
            return response.json()

        return response.content


class OpenvStorageClient(BaseResource):
    def __init__(self, ip, credentials, verify=False):
        super(OpenvStorageClient, self).__init__(requests.Session(), 'https://{}:443/api/'.format(ip))
        self._session.verify = verify
        self._session.headers['Accept'] = 'application/json; version=*'
        self._credentials = HTTPBasicAuth(*credentials)

    def login(self):
        data = self.oauth2.token('post', data={'grant_type': 'client_credentials'}, auth=self._credentials)
        token = data['access_token']
        self._session.headers['Authorization'] = 'Bearer {}'.format(token)
