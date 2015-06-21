from .client import Client
class ClientFactory(object):
    def get(self, url):
        return Client(url)

