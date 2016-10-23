from requests.auth import HTTPBasicAuth
from JumpScale.lib.openvstorage.client import OVSClient
import requests
from JumpScale import j


class OpenvStorageFactory(object):

    def _cache_token(self, token):
        redis_client = j.clients.redis.getByInstance('system')
        redis_client.set('ovs_rest_api_access_code', token)

    def get(self, ips, credentials, verify=False):
        """
        Gets dynamic client for OpenvStorageClient

        """
        redis_client = j.clients.redis.getByInstance('system')
        token = redis_client.get('ovs_rest_api_access_code')
        while ips:
            ip = ips.pop()
            try:
                connection = OVSClient(ip, 443, credentials, verify,
                                       cached_token=token,
                                       cache_token=self._cache_token)
                connection.get('/')  # Test that we have a working connection
                return connection
            except (requests.ConnectionError, RuntimeError):
                # TODO: fix except of RuntimeError ovs client doesnt pass http error for generic errors :(
                if not ips:
                    raise
