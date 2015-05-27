from fabric.api import settings
from StringIO import StringIO

from .base import BaseService


class DNSError(Exception):
    pass


class DNS(BaseService):
    PACKAGE = 'dhcp'
    HOSTS = '/tmp/hosts/jumpscale'

    ADD_OP = '+'
    REM_OP = '-'
    REMALL_OP = '--'

    def __init__(self, wrt):
        super(DNS, self).__init__(wrt)
        self._transactions = list()

    @property
    def domain(self):
        """
        Get DNS domain
        """
        dnsmasq = self.package.find('dnsmasq')
        if not dnsmasq:
            return ''
        section = dnsmasq[0]
        return section['domain']

    @domain.setter
    def domain(self, value):
        """
        Set DNS domain
        """
        dnsmasq = self.package.find('dnsmasq')
        if not dnsmasq:
            section = self._wrt.add('dnsmasq')
        else:
            section = dnsmasq[0]

        section['domain'] = value
        section['local'] = '/%s/' % value

    @property
    def records(self):
        """
        Return all custom DNS A records
        """
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

    def _runTransactions(self):
        # write hosts
        records = self.records
        while self._transactions:
            trans = self._transactions.pop(0)
            op, name, ip = trans
            if op == DNS.ADD_OP:
                records.setdefault(name, list())
                records[name].append(ip)
            elif op == DNS.REM_OP:
                if name not in records:
                    continue
                if ip is None:
                    del records[name]
                elif ip in records[name]:
                    records[name].remove(ip)
            elif op == DNS.REMALL_OP:
                records = {}
        return records

    def commit(self):
        """
        Apply any pending changes and restart DNS
        """
        # write main dns uci
        self._wrt.commit(self.package)

        records = self._runTransactions()
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

    def erase(self):
        """
        Remove all hosts (A records)
        """
        self._transactions.append((DNS.REMALL_OP, None, None))
