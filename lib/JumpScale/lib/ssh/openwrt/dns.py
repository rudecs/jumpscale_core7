from fabric.api import settings
from StringIO import StringIO


class DNSError(Exception):
    pass


class DNS(object):
    PACKAGE = 'dhcp'
    HOSTS = '/tmp/hosts/jumpscale'

    ADD_OP = '+'
    REM_OP = '-'

    def __init__(self, wrt):
        self._wrt = wrt
        self._package = None
        self._transactions = list()

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

    @property
    def records(self):
        con = self._wrt.connection
        with settings(shell=self._wrt.WRT_SHELL, abort_exception=DNSError):
            if not con.file_exists(DNS.HOSTS):
                return {}

            hosts = {}
            # we can't use file_read on open-wrt because it doesn't have
            # openssl by default. We use cat instead
            hostsstr = con.run('cat %s' % DNS.HOSTS)
            for line in hostsstr.split('\n'):
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue
                ip, name = line.split(' ', 2)
                hosts.setdefault(name, list())
                hosts[name].append(ip)
            return hosts

    def _applyTransactions(self):
        # write hosts
        records = self.records
        for trans in self._transactions:
            op, name, ip = trans
            if op == DNS.ADD_OP:
                records.setdefault(name, list())
                records[name].append(ip)
            if op == DNS.REM_OP:
                if name not in records:
                    continue
                if ip is None:
                    del records[name]
                elif ip in records[name]:
                    records[name].remove(ip)
        return records

    def commit(self):
        """
        Apply any pending changes and restart DNS
        """
        # write main dns uci
        self._wrt.commit(self.package)

        records = self._applyTransactions()
        command = StringIO()
        command.write('cat > {file} <<HOSTS\n'.format(file=DNS.HOSTS))
        for host, ips in records.iteritems():
            for ip in ips:
                command.write('%s %s\n' % (ip, host))

        command.write('\nHOSTS\n')
        con = self._wrt.connection
        with settings(shell=self._wrt.WRT_SHELL, abort_exception=DNSError):
            # write hosts file
            con.run(command.getvalue())

            # restart dnsmasq
            con.run('/etc/init.d/dnsmasq restart')

    def addARecord(self, name, ip):
        """
        Add A record to DNS

        :name: Host name
        :ip: Host IP
        """
        self._transactions.append((DNS.ADD_OP, name, ip))

    def removeARecord(self, name, ip=None):
        """
        Remove A record from DNS

        :name: Host name
        :ip: Host IP, if None, remove all A records for the named host
        """
        self._transactions.append((DNS.REM_OP, name, ip))
