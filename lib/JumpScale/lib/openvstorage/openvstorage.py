from requests.auth import HTTPBasicAuth
from JumpScale.lib.openvstorage.client import OVSClient
import requests
import redis
from JumpScale import j


class OpenvStorageFactory(object):

    def _cache_token(self, token):
        redis_client = j.clients.redis.getByInstance('system')
        try:
            redis_client.set('ovs_rest_api_access_code', token)
        except redis.exceptions.ConnectionError:
            pass

    def get(self, ips, credentials, verify=False):
        """
        Gets dynamic client for OpenvStorageClient

        """
        redis_client = j.clients.redis.getByInstance('system')
        try:
            token = redis_client.get('ovs_rest_api_access_code')
        except redis.exceptions.ConnectionError:
            token = None
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
