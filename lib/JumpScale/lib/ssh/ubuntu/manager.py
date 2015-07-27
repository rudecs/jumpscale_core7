from .network import NetworkManager
from JumpScale import j

class UbuntuManagerFactory(object):
    def get(self, connection=None):
        """
        Returns Ubuntu Manager
        """
        return UbuntuManager(connection)

class UbuntuManager(object):
    """
    Ubuntu Manager
    """
    def __init__(self, connection=None):
        if connection==None:
            connection=j.ssh.connection

        self._con = connection
        self._net = NetworkManager(self)

    @property
    def connection(self):
        """
        Connection manager
        """
        return self._con

    @property
    def network(self):
        """
        Network manager
        """
        return self._net

