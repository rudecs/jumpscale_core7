from JumpScale import j
import json
import urllib

class VirtualMachinesFactory(object):
    def get(self, target, settings={}):
        return VirtualMachines(target, settings)

class VirtualMachines(object):
    def __init__(self, target, settings):
        self.targets = ['ms1', 'docker']
        self.target = target
        
        self._mother = {
            'apiurl': 'www.mothership1.com',
            'secret': '',
            'api': None,
            'image': 'ubuntu.14.04.x64',
            'cloudspace': '',
            'location': '',
            'sshkey': '/root/.ssh/id_rsa.pub'
        }
        
        self._docker = {
            'remote': None,
            'port': '',
            'api': None,
            'image': 'jumpscale/ubuntu1404',
            'public': ''
        }
        
        self.docking = {}
        
        # target validator
        if target not in self.targets:
            raise NameError('Target "%s" not available')
        
        # custom validators and loader
        if target == 'ms1':
            self.info('setting up backend: mothership1')
            
            # validator
            if not settings.get('secret'):
                raise NameError('Missing mothership1 option: secret')
            
            if not settings.get('cloudspace'):
                raise NameError('Missing mothership1 option: cloudspace')
            
            if not settings.get('location'):
                raise NameError('Missing mothership1 option: location')
            
            if settings.get('apiurl'):
                self._mother['apiurl'] = settings['apiurl']
            
            # copy settings
            self._mother['api']        = j.tools.ms1.get(self._mother['apiurl'])
            self._mother['secret']     = settings['secret']
            self._mother['cloudspace'] = settings['cloudspace']
            self._mother['location']   = settings['location']
            
            self.message('loading mothership1 api: %s' % self._mother['apiurl'])
            self._mother['api'].setCloudspace(self._mother['secret'], self._mother['cloudspace'], self._mother['location'])
        
        if target == 'docker':
            self.info('setting up backend: docker')
            
            # validator
            if not settings.get('public'):
                raise NameError('Missing docker option: public (host public ip address)')
            
            # copy settings
            if settings.get('remote'):
                self._docker['remote'] = settings['remote']
                
            if settings.get('port'):
                self._docker['port'] = settings['port']
            
            self._docker['api'] = j.tools.docker
            
            if self._docker['remote']:
                self.message('connecting remote server: %s/%s' % (self._docker['remote'], self._docker['port']))
                self._docker['api'].connectRemoteTCP(self._docker['remote'], self._docker['port'])
            
            self._docker['public'] = settings['public']

    
    # FIXME: move me
    def info(self, text):
        print '\033[1;36m[*] %s\033[0m' % text
        
    def warning(self, text):
        print '\033[1;33m[-] %s\033[0m' % text

    def success(self, text):
        print '\033[1;32m[+] %s\033[0m' % text
    
    def message(self, text):
        print '\033[0m[+] %s\033[0m' % text
    
    
    #
    # machine creation
    #
    def _ms1_createMachine(self, hostname, memsize, ssdsize, delete):
        # FIXME: remove this try/catch ?
        try:
            self._mother['api'].createMachine(self._mother['secret'], hostname, memsize=memsize, ssdsize=ssdsize, imagename=self._mother['image'], sshkey=self._mother['sshkey'], delete=delete)
        
        except Exception as e:
            if e.message.find('Could not create machine it does already exist') == -1:
                raise e
    
    def _docker_createMachine(self, hostname, memsize):
        self.docking[hostname] = {
            'memsize': memsize,
            'status': 'waiting',
            'ports': []
        }
        
        return self.docking[hostname]
    
    #
    # machine grabber
    #
    def _ms1_getMachine(self, hostname):
        item = self._mother['api'].getMachineObject(self._mother['secret'], hostname)
        ports = self._mother['api'].listPortforwarding(self._mother['secret'], hostname)
        
        for fw in ports:
            if fw['localPort'] == '22':
                sshforward = fw
        
        data = {
            'hostname': item['name'],
            'localport': sshforward['localPort'],
            'localip': str(item['interfaces'][0]['ipAddress']),
            'publicip': sshforward['publicIp'],
            'publicport': str(sshforward['publicPort']),
            'image': item['osImage']
        }
        
        return data
    
    def _docker_getMachine(self, hostname):
        dock = self._docker['api'].client.inspect_container(hostname)
        
        data = {
            'hostname': dock['Config']['Hostname'],
            'localport': 22,
            'localip': dock['NetworkSettings']['IPAddress'],
            'publicip': self._docker['public'],
            'publicport': dock['HostConfig']['PortBindings']['22/tcp'][0]['HostPort'],
            'image': dock['Config']['Image']
        }
        
        return data
    
    #
    # machine commit
    #
    def _docker_commit(self, hostname):
        if self.docking.get(hostname) == None:
            return False
        
        # building exposed ports
        ports = ' '.join(self.docking[hostname]['ports'])
        
        port = self._docker['api'].create(name=hostname, ports=ports, base=self._docker['image'], mapping=False)
        return self._docker_getMachine(hostname)
    
    #
    # ports forwarder
    #
    def _ms1_portForward(self, hostname, localport, publicport):
        return self._mother['api'].createTcpPortForwardRule(self._mother['secret'], hostname, localport, pubipport=publicport)
    
    def _docker_portForward(self, hostname, localport, publicport):
        if self.docking.get(hostname) == None:
            raise NameError('Hostname "%s" seems not ready for docker settings' % hostname)
            
        self.docking[hostname]['ports'].append('%s:%s' % (localport, publicport))
        return True
    
    #
    # public interface
    #
    def getMachine(self, hostname):
        self.message('grabbing settings for: %s' % hostname)
        
        if self.target == 'ms1':
            return self._ms1_getMachine(hostname)
        
        raise NameError('Target "%s" is not supported' % self.target)
    
    def createMachine(self, hostname, memsize, ssdsize, delete):
        self.info('initializing: %s (RAM: %s GB, Disk: %s GB)' % (hostname, memsize, ssdsize))
        
        if self.target == 'ms1':
            return self._ms1_createMachine(hostname, str(memsize), str(ssdsize), delete)
        
        if self.target == 'docker':
            return self._docker_createMachine(hostname, memsize)
        
        raise NameError('Target "%s" is not supported' % self.target)
    
    def createPortForward(self, hostname, localport, publicport):
        self.info('port forwarding: %s (%s -> %s)' % (hostname, publicport, localport))
        
        if self.target == 'ms1':
            return self._ms1_portForward(hostname, localport, publicport)
        
        if self.target == 'docker':
            return self._docker_portForward(hostname, localport, publicport)
        
        raise NameError('Target "%s" is not supported' % self.target)
    
    def commitMachine(self, hostname):
        self.info('commit: %s' % hostname)
        
        if self.target == 'ms1':
            return self.getMachine(hostname)
        
        if self.target == 'docker':
            return self._docker_commit(hostname)
        
        raise NameError('Target "%s" is not supported' % self.target)
    
    
    """
    Console tools
    """
    def enableQuiet(self, remote=None):
        j.remote.cuisine.api.fabric.state.output['stdout'] = False
        j.remote.cuisine.api.fabric.state.output['running'] = False
        
        if remote:
            remote.fabric.state.output['stdout'] = False
            remote.fabric.state.output['running'] = False
    
    def disableQuiet(self, remote=None):
        j.remote.cuisine.api.fabric.state.output['stdout'] = True
        j.remote.cuisine.api.fabric.state.output['running'] = True
        
        if remote:
            remote.fabric.state.output['stdout'] = True
            remote.fabric.state.output['running'] = True
