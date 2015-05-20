from StringIO import StringIO

from fabric.api import settings

from .uci import UCI
from .dns import DNS


class UCIError(Exception):
    pass


class OpenWRTFactory(object):
    def get(self, connection):
        """
        Return disk manager for that cuisine connection.
        """
        return OpenWRTManager(connection)


class OpenWRTManager(object):
    WRT_SHELL = '/bin/ash -c'

    def __init__(self, con):
        self._con = con
        self._dns = DNS(self)

    @property
    def dns(self):
        return self._dns

    def get(self, name):
        """
        Loads package UCI from openwrt, or new package if doesn't exit
        """
        uci = UCI(name)
        try:
            with settings(shell=self.WRT_SHELL, abort_exception=UCIError):
                ucistr = self._con.run('uci export %s' % name)
            uci.loads(ucistr)
        except UCIError:
            pass

        return uci

    def commit(self, uci):
        buffer = StringIO()
        buffer.write('uci import {package} <<UCI\n'.format(
            package=uci.package
        ))

        uci.dump(buffer)

        buffer.write('\nUCI\n')

        command = buffer.getvalue()

        with settings(shell=self.WRT_SHELL, abort_exception=UCIError):
            self._con.run(command)
