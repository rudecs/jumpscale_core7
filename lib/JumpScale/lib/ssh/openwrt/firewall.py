from fabric.api import settings

from .base import BaseService, BaseServiceSection


class FirewallError(Exception):
    pass


class Redirect(BaseServiceSection):
    EXPOSED_FIELDS = [
        'target',
        'src',
        'dest',
        'proto',
        'src_dport',
        'dest_ip',
        'dest_port',
        'name',
    ]

    def __str__(self):
        return ('({proto}) {src_dport}:{src} -> '
                '{dest}:{dest_ip}:{dest_port}').format(
            proto=self.proto,
            src=self.src,
            src_dport=self.src_dport,
            dest=self.dest,
            dest_ip=self.dest_ip,
            dest_port=self.dest_port
        )

    def __repr__(self):
        return str(self)


class Firewall(BaseService):
    PACKAGE = 'firewall'

    @property
    def zones(self):
        return map(lambda s: s['name'], self.package.find('zone'))

    @property
    def redirects(self):
        return map(Redirect, self.package.find('redirect'))

    def addRedirect(self, name):
        red = Redirect(self.package.add('redirect'))
        red.name = name
        return red

    def removeRedirect(self, redirect):
        self.package.remove(redirect.section)

    def commit(self):
        self._wrt.commit(self.package)

        con = self._wrt.connection
        with settings(shell=self._wrt.WRT_SHELL,
                      abort_exception=FirewallError):
            # restart ftp
            con.run('/etc/init.d/firewall restart')
