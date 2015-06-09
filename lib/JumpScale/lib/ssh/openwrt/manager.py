import os
from StringIO import StringIO

from fabric.api import settings

from .uci import UCI
from .dns import DNS
from .dhcp import DHCP
from .pureftp import PureFTP
from .network import Network
from .firewall import Firewall

from JumpScale import j


WRITE_CHUNK_SIZE = 512


class UCIError(Exception):
    pass


class OpenWRTFactory(object):
    def get(self, connection=None):
        """
        Return disk manager for that cuisine connection.
        """
        if connection==None:
            connection=j.ssh.connection

        return OpenWRTManager(connection)


class OpenWRTManager(object):
    WRT_SHELL = '/bin/ash -c'

    def __init__(self, con):
        self._con = con
        self._dns = DNS(self)
        self._dhcp = DHCP(self)
        self._ftp = PureFTP(self)
        self._network = Network(self)
        self._firewall = Firewall(self)

    @property
    def connection(self):
        return self._con

    @property
    def dns(self):
        """
        DNS abstraction on top of UCI
        """
        return self._dns

    @property
    def dhcp(self):
        """
        DHCP abstraction on top of UCI
        """
        return self._dhcp

    @property
    def ftp(self):
        """
        PureFTP abstraction on top of UCI
        """
        return self._ftp

    @property
    def network(self):
        return self._network

    @property
    def firewall(self):
        return self._firewall

    def get(self, name):
        """
        Loads UCI package from openwrt, or new package if name doesn't exit

        :name: package name (ex: network, system, etc...)
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
        """
        Commint uci package to openwrt.
        """
        buffer = StringIO()
        buffer.write('uci import {package} <<UCI\n'.format(
            package=uci.package
        ))

        uci.dump(buffer)

        buffer.write('\nUCI\n')
        # command = buffer.getvalue()

        with settings(shell=self.WRT_SHELL, abort_exception=UCIError):
            buffer.seek(0)
            chunk = buffer.read(WRITE_CHUNK_SIZE)
            if len(chunk) < WRITE_CHUNK_SIZE:
                self._con.run(chunk)
                return

            # Write chunks into file
            tmp = os.tempnam()
            try:
                self._con.run(
                    'echo -n > {tmp} "{chunk}"'.format(
                        tmp=tmp,
                        chunk=chunk
                    )
                )

                while True:
                    chunk = buffer.read(WRITE_CHUNK_SIZE)
                    if not chunk:
                        break
                    self._con.run(
                        'echo -n >> {tmp} "{chunk}"'.format(
                            tmp=tmp,
                            chunk=chunk
                        )
                    )

                self._con.run('chmod +x %s' % tmp)
                self._con.run(tmp)
            finally:
                self._con.run('rm -f %s')
