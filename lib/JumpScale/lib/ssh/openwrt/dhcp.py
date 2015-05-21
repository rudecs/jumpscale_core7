from fabric.api import settings


class DHCPError(Exception):
    pass


class Interface(object):
    def __init__(self, section):
        self._section = section

    @property
    def section(self):
        """
        The low level UCI section
        """
        return self._section

    @property
    def name(self):
        """
        Interface name
        """
        return self._section['interface']

    @property
    def start(self):
        """
        Lowest leased address as offset from the network address
        """
        return self._section.get('start')

    @start.setter
    def start(self, value):
        self._section['start'] = value

    @property
    def limit(self):
        """
        Maximum number of leased addresses.
        """
        return self._section.get('limit')

    @limit.setter
    def limit(self, value):
        self._section['limit'] = value

    @property
    def leasetime(self):
        """
        Expiry time of leased addresses, minimum is 2 minutes (2m).
        """
        return self._section.get('leasetime')

    @leasetime.setter
    def leasetime(self, value):
        self._section['leasetime'] = value

    @property
    def enabled(self):
        """
        Enable DHCP on this interface
        """
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
        """
        The low level UCI section for that host
        """
        return self._section

    @property
    def name(self):
        """
        Host name
        """
        return self._section['name']

    @name.setter
    def name(self, value):
        self._section['name'] = value

    @property
    def mac(self):
        """
        Host MAC
        """
        return self._section['mac']

    @mac.setter
    def mac(self, value):
        self._section['mac'] = value

    @property
    def ip(self):
        """
        Host IP
        """
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


class PXE(object):
    def __init__(self, section):
        self._section = section

    @property
    def section(self):
        return self._section

    @property
    def filename(self):
        return self._section.get('filename', '')

    @filename.setter
    def filename(self, value):
        self._section['filename'] = value

    @property
    def serveraddress(self):
        return self._section.get('serveraddress', '')

    @serveraddress.setter
    def serveraddress(self, value):
        self._section['serveraddress'] = value

    @property
    def servername(self):
        return self._section.get('servername', '')

    @servername.setter
    def servername(self, value):
        self._section['servername'] = value

    @property
    def options(self):
        options = self._section.get('dhcp_option', list())
        # make sure it's a list of options
        if not isinstance(options, list):
            options = [options]
            self._options['dhcp_option'] = options

        return options

    def __str__(self):
        return ('pxe %s%s' % (self.serveraddress, self.filename)).strip()

    def __repr__(self):
        return str(self)


class DHCP(object):
    PACKAGE = 'dhcp'

    def __init__(self, wrt):
        self._wrt = wrt
        self._package = None

    @property
    def package(self):
        """
        The low level UCI interface
        """
        if self._package is None:
            self._package = self._wrt.get(DHCP.PACKAGE)
        return self._package

    @property
    def pxe(self):
        sections = self.package.find('boot', 'linux')
        if not sections:
            section = self.package.add('boot', 'linux')
        else:
            section = sections[0]

        return PXE(section)

    @property
    def interfaces(self):
        """
        Returns all interfaces
        """
        # wrap the UCI sections in Interface obj
        return map(Interface, self.package.find('dhcp'))

    @property
    def hosts(self):
        """
        Return all static hosts
        """
        return map(Host, self.package.find('host'))

    def addHost(self, name, mac, ip):
        """
        Add static host

        :name: host name
        :mac: host mac
        :ip: host IP
        """
        sec = self.package.add('host')
        sec['name'] = name
        sec['mac'] = mac
        sec['ip'] = ip

        return Host(sec)

    def removeHost(self, name):
        """
        Remove static host

        :name: host name
        """
        for host in self.hosts:
            if host.name == name:
                self.package.remove(host.section)
                return

    def erase(self):
        """
        Remove all static hosts
        """
        for sec in self.package.find('host'):
            self.package.remove(sec)

    def commit(self):
        """
        Commit changes to openwrt and restart DHCP
        """
        self._wrt.commit(self.package)

        con = self._wrt.connection
        with settings(shell=self._wrt.WRT_SHELL, abort_exception=DHCPError):
            # restart dnsmasq
            con.run('/etc/init.d/dnsmasq restart')
