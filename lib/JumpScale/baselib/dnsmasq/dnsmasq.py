from JumpScale import j
import signal


DOMAIN = 'network'

class DNSMasq(object):

    def __init__(self):
        self._configured = False

    def setConfigPath(self, namespace=None, config_path=None):
        if not config_path:
            self._configdir = j.system.fs.joinPaths('/etc', 'dnsmasq')
        else:
            self._configdir = config_path
        if not j.system.platform.ubuntu.findPackagesInstalled('dnsmasq'):
            j.system.platform.ubuntu.install('dnsmasq')
        self._hosts = j.system.fs.joinPaths(self._configdir, 'hosts')
        self._pidfile = j.system.fs.joinPaths(self._configdir, 'dnsmasq.pid')
        self._leasesfile = j.system.fs.joinPaths(self._configdir, 'dnsmasq.leases')
        self._configfile = j.system.fs.joinPaths(self._configdir, 'dnsmasq.conf')
        if namespace:
            self._namespace = namespace
            self._startupmanagername = 'dnsmasq_%s' % (namespace)
        else: 
            self._startupmanagername = 'dnsmasq'
        startname = '%s__%s' % ('network', self._startupmanagername)
        if startname not in j.tools.startupmanager.listProcesses():
            self.addToStartupManager()
        self._configured = True

    
    def addToStartupManager(self):
        if self._namespace:
            cmd = 'ip netns exec %(namespace)s dnsmasq -k --conf-file=%(configfile)s --pid-file=%(pidfile)s --dhcp-hostsfile=%(hosts)s --dhcp-leasefile=%(leases)s' % {'namespace':self._namespace,'configfile':self._configfile, 'pidfile': self._pidfile, 'hosts': self._hosts, 'leases': self._leasesfile}
        else:
            cmd = 'dnsmasq -k --conf-file=%(configfile)s --pid-file=%(pidfile)s --dhcp-hostsfile=%(hosts)s --dhcp-leasefile=%(leases)s' % {'configfile':self._configfile, 'pidfile': self._pidfile, 'hosts': self._hosts, 'leases': self._leasesfile}
        j.tools.startupmanager.addProcess(self._startupmanagername, cmd, reload_signal=signal.SIGHUP, domain=DOMAIN)
        j.tools.startupmanager.startProcess(DOMAIN, self._startupmanagername)

    
    def _checkFile(self, filename):
        if not j.system.fs.exists(filename):
            j.system.fs.createEmptyFile(filename)
         

    def addHost(self, macaddress, ipaddress, name=None):
        if not self._configured:
            raise Exception('Please run first setConfigPath to select the correct paths')
        """Adds a dhcp-host entry to dnsmasq.conf file"""
        self._checkFile(self._hosts)
        te = j.codetools.getTextFileEditor(self._hosts)
        contents = '%s' % macaddress
        if name:
            contents += ',%s' % name
        contents += ',%s\n' % ipaddress
        te.appendReplaceLine('.*%s.*' % macaddress, contents)
        te.save()
        self.reload()

    def removeHost(self, macaddress):
        """Removes a dhcp-host entry from dnsmasq.conf file"""
        if not self._configured:
            raise Exception('Please run first setConfigPath to select the correct paths')
        self._checkFile(self._hosts)
        te = j.codetools.getTextFileEditor(self._hosts)
        te.deleteLines('.*%s.*' % macaddress)
        te.save()
        self.reload()

    def restart(self):
        """Restarts dnsmasq"""
        if not self._configured:
            raise Exception('Please run first setConfigPath to select the correct paths')
        j.tools.startupmanager.load()
        j.tools.startupmanager.restartProcess(DOMAIN, self._startupmanagername)

    def reload(self):
        if not self._configured:
            raise Exception("Please run first setConfigPath to select the correct paths")
        j.tools.startupmanager.load()
        j.tools.startupmanager.reloadProcess(DOMAIN, self._startupmanagername)
