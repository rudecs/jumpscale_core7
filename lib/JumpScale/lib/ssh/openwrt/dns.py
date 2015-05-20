from fabric.api import settings


class DNSError(Exception):
    pass


class DNS(object):
    PACKAGE = 'dhcp'

    def __init__(self, wrt):
        self._wrt = wrt
        self._package = None

    @property
    def package(self):
        if self._package is None:
            self._package = self._wrt.get(self.PACKAGE)

        return self._package

    @property
    def domain(self):
        dnsmasq = self.package.find('dnsmasq')
        if not dnsmasq:
            return ''
        section = dnsmasq[0]
        return section['domain']

    @domain.setter
    def domain(self, value):
        dnsmasq = self.package.find('dnsmasq')
        if not dnsmasq:
            section = self._wrt.add('dnsmasq')
        else:
            section = dnsmasq[0]

        section['domain'] = value

    def commit(self):
        self._wrt.commit(self.package)
        with settings(shell=self._wrt.WRT_SHELL, abort_exception=DNSError):
            self.con.run('/etc/init.d/dnsmasq restart')

    def addARecord(self):
        # write record to /tmp/dhcp/jumpscale
        # format:
        # <ip> <name>
        # same name can have multiple IPs

        pass
