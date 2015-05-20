from StringIO import StringIO

from fabric.api import settings

from .uci import UCI

WRT_SHELL = '/bin/ash -c'


class UCIException(Exception):
    pass


class OpenWRTFactory(object):
    def get(self, connection):
        """
        Return disk manager for that cuisine connection.
        """
        return OpenWRTManager(connection)


class OpenWRTManager(object):
    def __init__(self, con):
        self._con = con

    def get(self, name):
        """
        Loads package UCI from openwrt, or new package if doesn't exit
        """
        uci = UCI(name)
        try:
            with settings(shell=WRT_SHELL, abort_exception=UCIException):
                ucistr = self._con.run('uci export %s' % name)
            uci.loads(ucistr)
        except UCIException:
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

        with settings(shell=WRT_SHELL, abort_exception=UCIException):
            self._con.run(command)
