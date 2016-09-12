from requests.auth import HTTPBasicAuth
from JumpScale.lib.openvstorage.client import OVSClient
import requests

class OpenvStorageFactory(object):

    def get(self, ips, credentials, verify=False):
        """
        Gets dynamic client for OpenvStorageClient

        """
        while ips:
            ip = ips.pop()
            try:
                connection = OVSClient(ip, 443, credentials, verify)
                connection.get('/')  # Test that we have a working connection
                return connection
            except requests.ConnectionError:
                if not ips:
                    raise
