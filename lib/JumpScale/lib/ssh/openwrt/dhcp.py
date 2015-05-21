from fabric.api import settings


class DHCPError(Exception):
    pass


class Interface(object):
    def __init__(self, section):
        self._section = section

    @property
    def section(self):
        return self._section

    @property
    def name(self):
        return self._section['interface']

    @property
    def start(self):
        return self._section.get('start')

    @start.setter
    def start(self, value):
        self._section['start'] = value

    @property
    def limit(self):
        return self._section.get('limit')

    @limit.setter
    def limit(self, value):
        self._section['limit'] = value

    @property
    def leasetime(self):
        return self._section.get('leasetime')

    @leasetime.setter
    def leasetime(self, value):
        self._section['leasetime'] = value

    @property
    def enabled(self):
        return not bool(self._section.get('ignore'))

    @enabled.setter
    def enabled(self, value):
        self._section['ignore'] = not value

    def __str__(self):
        return 'interface %s' % self.name

    def __repr__(self):
        return str(self)


class Host(object):
    def __init__(self, section):
        self._section = section

    @property
    def section(self):
        return self._section

    @property
    def name(self):
        return self._section['name']

    @name.setter
    def name(self, value):
        self._section['name'] = value

    @property
    def mac(self):
        return self._section['mac']

    @mac.setter
    def mac(self, value):
        self._section['mac'] = value

    @property
    def ip(self):
        return self._section['ip']

    @ip.setter
    def ip(self, value):
        self._section['ip'] = value

    def __str__(self):
        return '{name} {mac} {ip}'.format(
            name=self.name,
            mac=self.mac,
            ip=self.ip
        )

    def __repr__(self):
        return str(self)


class DHCP(object):
    PACKAGE = 'dhcp'

    def __init__(self, wrt):
        self._wrt = wrt
        self._package = None

    @property
    def package(self):
        if self._package is None:
            self._package = self._wrt.get(DHCP.PACKAGE)
        return self._package

    @property
    def interfaces(self):
        """
        Returns all interfaces
        """
        # wrap the UCI sections in Interface obj
        return map(Interface, self.package.find('dhcp'))

    @property
    def hosts(self):
        return map(Host, self.package.find('host'))

    def addHost(self, name, mac, ip):
        sec = self.package.add('host')
        sec['name'] = name
        sec['mac'] = mac
        sec['ip'] = ip

        return Host(sec)

    def removeHost(self, name):
        for host in self.hosts:
            if host.name == name:
                self.package.remove(host.section)
                return

    def commit(self):
        self._wrt.commit(self.package)

        con = self._wrt.connection
        with settings(shell=self._wrt.WRT_SHELL, abort_exception=DHCPError):
            # restart dnsmasq
            con.run('/etc/init.d/dnsmasq restart')
