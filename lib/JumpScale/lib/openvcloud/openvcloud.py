from JumpScale import j
import urllib
import time
import sys


class OpenvcloudFactory(object):

    def get(self):
        return Openvclcoud()


class Openvclcoud(object):

    def __init__(self):
        self.reset = False
        self.db = j.db.keyvaluestore.getFileSystemStore("aysgit")
        self.masters = ['ovc_master', 'ovc_proxy', 'ovc_reflector', 'ovc_dcpm']

        self._ms1 = {}
        self._docker = {}
        self.bootstrapPort = '5000'

    def initLocalhost(self, gitlaburl, gitlablogin, gitlabpasswd):
        self.preprocess()

        if gitlablogin is None:
            j.console.warning("no gitlab check will be done, using github")
            return

        j.console.info("creating git repository")

        if gitlaburl.find("@") != -1:
            j.events.inputerror_critical('[-] do not use "login:passwd@" in the url')

        if not gitlaburl.startswith("http"):
            gitlaburl = "https://%s" % gitlaburl

        gitlabAccountname, gitlabReponame = j.clients.gitlab.getAccountnameReponameFromUrl(gitlaburl)
        gitlaburl0 = "/".join(gitlaburl.split("/")[:3])

        j.console.info('git group: %s' % gitlabAccountname)
        j.console.info('environment: %s' % gitlabReponame)

        gitlab = j.clients.gitlab.get(gitlaburl0, gitlablogin, gitlabpasswd)

        j.console.info('checking for existing project')

        projects = gitlab.getProjects(False)
        for project in projects:
            if project['name'] == gitlabReponame and project['namespace']['name'] == gitlabAccountname:
                j.console.warning('%s/%s: project already exists' % (gitlabAccountname, gitlabReponame))
                j.application.stop()

    def initMothership(self, login, passwd, location, cloudspace, reset=False, apiurl='www.mothership1.com'):
        j.console.info('building mothership1 based environment')

        api = j.tools.ms1.get(apiurl)
        secret = api.getCloudspaceSecret(login, passwd, cloudspace, location)

        self._ms1 = {
            'username': login,
            'password': passwd,
            'cloudspace': cloudspace,
            'location': location,
            'secret': secret
        }

        vm = j.clients.vm.get('ms1', self._ms1)

        machine = self.initMachine(vm, 'ms1', self._ms1)

        return {'remote': machine['publicip'], 'port': machine['publicport'], 'secret': secret, 'public': machine['publicip']}

    def initDocker(self, host, port, public):
        j.console.info('building docker based environment')

        j.console.info('preparing base image')
        today = time.strftime('%Y-%m-%d')
        image = 'openvcloud/%s' % today

        self._docker = {
            'remote': host,
            'port': port,
            'public': public,
            'image': image
        }

        vm = j.clients.vm.get('docker', self._docker)

        # checking if image already exists
        images = vm._docker['api'].getImages()

        if image not in images:
            print '[+] building the image'

            args = {'instance.image.name': image}
            j.atyourservice.remove(name='docker_ovc')
            service = j.atyourservice.new(name='docker_ovc', args=args)
            service.install(reinstall=False)

        else:
            j.console.info('image already made, re-using it...')

        machine = self.initMachine(vm, 'docker', self._docker)

        return {'remote': host, 'port': machine['publicport'], 'public': public, 'image': image}

    def initMachine(self, vm, target, settings):
        sshport = 22 if target != 'docker' else 2202

        vm.createMachine('ovc_git', memsize='0.5', ssdsize='10', delete=True)
        vm.createPortForward('ovc_git', 22, sshport)
        vm.createPortForward('ovc_git', self.bootstrapPort, self.bootstrapPort)
        vm.commitMachine('ovc_git')

        machine = vm.getMachine('ovc_git')

        return machine

    def preprocess(self):
        j.console.info("checking local ssh key")

        keypath = '/root/.ssh/id_rsa'

        if not j.system.fs.exists(path=keypath):
            j.console.info("generating local rsa key")
            j.system.platform.ubuntu.generateLocalSSHKeyPair()

        j.console.info('checking for redis')
        if not j.system.net.tcpPortConnectionTest("localhost", 9999, timeout=None):
            redis = j.atyourservice.findServices(instance='system', name='redis')

            if len(redis) == 0:
                j.console.warning('cannot continue, redis is not installed')
                j.application.stop()

            redis[0].start()

    def actionCheck(self, gitlaburl, actionname):
        if self.reset:
            return False

        key = "%s__%s" % (gitlaburl, actionname)

        if self.db.exists("", key):
            j.console.notice("action: %s already done" % actionname)
            return self.db.get("", key)

        return False

    def actionDone(self, gitlaburl, actionname, args=None):
        key = "%s__%s" % (gitlaburl, actionname)
        self.db.set("", key, args)

    def jumpscale(self, remote):
        if remote.file_exists('/opt/jumpscale7/'):
            j.console.info("jumpscale seems already installed, skipping")
            return

        j.console.info("installing jumpscale")
        cmd = j.do.getInstallCommand()
        remote.run(cmd)

    def initAYSGitVM(self, machine, gitlaburl, gitlablogin, gitlabpasswd, recoverypasswd, domain, environment, delete=False):
        keypath = '/root/.ssh/id_rsa'

        if len(recoverypasswd) < 6:
            j.events.inputerror_critical("[-] recovery passwd needs to be at least 6 chars")

        j.console.info('creating gitlab project')

        gitlabAccountname, gitlabReponame = j.clients.gitlab.getAccountnameReponameFromUrl(gitlaburl)
        gitlaburl0 = "/".join(gitlaburl.split("/")[:3])

        if gitlablogin:
            j.console.info('creating gitlab project')

            gitlaburl0 = "/".join(gitlaburl.split("/")[:3])

            gitlab = j.clients.gitlab.get(gitlaburl0, gitlablogin, gitlabpasswd)
            gitlab.createProject(gitlabAccountname, gitlabReponame, public=False)

        cl = j.ssh.connect(machine['remote'], machine['port'], keypath=keypath, verbose=True)

        j.console.info('generating keypair on the vm')
        cl.ssh_keygen('root', 'rsa')

        # install jumpscale
        self.jumpscale(cl)

        ovcversion = j.clients.git.get('/opt/code/github/0-complexity/openvcloud').getBranchOrTag()[1]

        j.console.info('adding openvcloud domain to atyourservice')
        content = "metadata.openvcloud            =\n"
        content += "    branch:'%s',\n" % (ovcversion)
        content += "    url:'git@github.com:0-complexity/openvcloud_ays',\n"

        cl.file_append('/opt/jumpscale7/hrd/system/atyourservice.hrd', content)

        # git credentials
        cl.run('jsconfig hrdset -n whoami.git.login -v "ssh"')
        cl.run('jsconfig hrdset -n whoami.git.passwd -v "ssh"')

        infos = {
            'name': ''
        }

        baseinfos = {
            'email': 'nobody@aydo.com',
            'name': gitlablogin if gitlablogin else 'gig setup'
        }

        if gitlablogin:
            infos = gitlab.getUserInfo(gitlablogin)

        email = infos['email'] if infos.has_key('email') else baseinfos['email']
        name = infos['name'] if infos['name'] != '' else baseinfos['name']

        cl.run('git config --global user.email "%s"' % email)
        cl.run('git config --global user.name "%s"' % name)

        allowhosts = ["github.com", "git.aydo.com"]

        for host in allowhosts:
            cl.run('echo "Host %s" >> /root/.ssh/config' % host)
            cl.run('echo "    StrictHostKeyChecking no" >> /root/.ssh/config')
            cl.run('echo "" >> /root/.ssh/config')

        if gitlablogin:
            repopath = "/opt/code/git/%s/%s/" % (gitlabAccountname, gitlabReponame)
            repoURL = 'git@git.aydo.com:%s/%s.git' % (gitlabAccountname, gitlabReponame)

        else:
            repopath = "/opt/code/github/%s/%s/" % (gitlabAccountname, gitlabReponame)
            repoURL = 'git@github.com:%s/%s.git' % (gitlabAccountname, gitlabReponame)

        if not cl.file_exists(repopath):
            cl.run('git clone git@github.com:gig-projects/env_template.git %s' % repopath)
            cl.run('cd %s; git remote set-url origin %s' % (repopath, repoURL))

            # Note: rebase prevents for asking to merge local tree with remote
            cl.run('cd %s; git pull --rebase' % repopath)

        # copy keys
        keys = {
            '/root/.ssh/id_rsa': (j.system.fs.joinPaths(repopath, 'keys', 'git_root'), ),
            '/root/.ssh/id_rsa.pub': (j.system.fs.joinPaths(repopath, 'keys', 'git_root.pub'), ),
        }

        for source, dests in keys.iteritems():
            content = cl.file_read(source)
            for dest in dests:
                cl.file_write(dest, content)
                cl.run('chmod 600 %s' % dest)

        # append key to authorized hosts
        cl.run("cat %s >> /root/.ssh/authorized_keys" % keys['/root/.ssh/id_rsa.pub'])

        # saving clients
        if machine['type'] == 'ms1':
            # create ms1_client to save ms1 connection info
            args = 'instance.param.location:%s ' % self._ms1['location']
            args += 'instance.param.login:%s ' % self._ms1['username']
            args += 'instance.param.passwd:%s ' % self._ms1['password']
            args += 'instance.param.cloudspace:%s' % self._ms1['cloudspace']

            cl.run('cd %s; ays install -n ms1_client --data "%s" -r' % (repopath, args))

        if machine['type'] == 'docker':
            # create ms1_client to save ms1 connection info
            args = 'instance.remote.host:%s ' % self._docker['remote']
            args += 'instance.remote.port:%s ' % self._docker['port']
            args += 'instance.public.address:%s ' % self._docker['public']
            args += 'instance.image.base:%s' % machine['image']

            cl.run('cd %s; ays install -n docker_client --data "%s" -r' % (repopath, args))

        # ensure that portal libs are installed
        cl.run('cd %s; ays install -n portal_lib -r' % repopath)

        # create ovc_setup instance to save settings
        args = 'instance.ovc.environment:%s ' % environment
        args += 'instance.ovc.path:%s ' % repopath
        args += 'instance.ovc.ms1.instance:main '           # FIXME, remove me
        args += 'instance.ovc.gitlab_client.instance:main '  # FIXME, remove me
        args += 'instance.ovc.password:%s ' % recoverypasswd
        args += 'instance.ovc.bootstrap.port:%s ' % self.bootstrapPort
        args += 'instance.ovc.bootstrap.host:%s ' % machine['remote']
        args += 'instance.ovc.cloudip:%s ' % machine['public']
        args += 'instance.ovc.gitip:%s ' % machine['remote']
        args += 'instance.ovc.domain:%s ' % domain

        cl.run('cd %s; ays install -n ovc_setup --data "%s" -r' % (repopath, args))

        # create ms1_client to save ms1 connection info
        args = 'instance.param.recovery.passwd:%s instance.param.ip:%s' % (recoverypasswd, machine['remote'])
        cl.run('cd %s; ays install -n git_vm --data "%s" -r' % (repopath, args))
        cl.run('git config --global push.default simple')
        cl.run('cd %s; jscode push' % repopath)

        cl.run('cd %s; ays install -n ovc_namer -r' % repopath)
        cl.run('cd %s; jscode push' % repopath)

        print '[+] setup completed'

        # check if netstat can gives pid
        lines = cl.run('netstat -anoptuw | grep sshd | wc -l')
        if int(lines) == 0:
            j.console.warning('WARNING: ************************************************************')
            j.console.warning('WARNING: no ssh pid found with netstat, this will break setup')
            j.console.warning('WARNING: - if you are using docker, you are not up-to-date')
            j.console.warning('WARNING: - otherwise, your system seems not correctly configured')
            j.console.warning('WARNING: ************************************************************')

        else:
            j.console.info('environment is ready to be deployed')

        # ensure that ssh agent is running and add the new key
        j.do.execute('eval $(ssh-agent -s)')

        j.console.info('you can now ssh the ovcgit host to configure the environment')
        j.console.info('  ssh root@%s -p %s -A' % (machine['remote'], machine['port']))

    def _getNodes(self):
        sshservices = j.atyourservice.findServices(name='node.ssh')
        sshservices.sort(key=lambda x: x.instance)
        return sshservices

    def getMasterNodes(self):
        sshservices = self._getNodes()
        nodes = []

        for ns in sshservices:
            if ns.instance in self.masters:
                nodes.append(ns)

        return nodes

    def getRemoteNodes(self):
        sshservices = self._getNodes()
        nodes = []

        for ns in sshservices:
            if ns.instance not in self.masters:
                nodes.append(ns)

        return nodes

    def getRemoteNode(self, nodename):
        j.console.info('Finding node {}'.format(nodename))
        services = j.atyourservice.findServices(name='node.ssh', instance=nodename)
        if len(services) != 1:
            raise KeyError("Could not find node {}".format(nodename))
        return services[0]

    def configureNginxProxy(self, node, settings, instance='http_proxy'):
        refsrv = j.atyourservice.findServices(name='node.ssh', instance='ovc_reflector')

        if len(refsrv) > 0:
            autossh = True
            reflector = refsrv[0]

            refaddress = reflector.hrd.getStr('instance.ip')
            refport = reflector.hrd.getStr('instance.ssh.publicport')

            if refport is None:
                j.console.warning('cannot find reflector public ssh port')
                return False

            # find autossh of this node
            autossh = next(iter(j.atyourservice.findServices(name='autossh', instance=node.instance)), None)
            if not autossh:
                j.console.warning('cannot find auto ssh of node')
                return autossh

            remoteport = autossh.hrd.getInt('instance.remote.port') - 21000 + 2000
            data_autossh = {'instance.local.address': 'localhost',
                            'instance.local.port': '2001',
                            'instance.remote.address': settings.getStr('instance.ovc.cloudip'),
                            'instance.remote.bind': refaddress,
                            'instance.remote.connection.port': refport,
                            'instance.remote.login': 'guest',
                            'instance.remote.port': remoteport,
                            }

            j.console.info('autossh tunnel port: %s' % data_autossh['instance.remote.port'])
            j.console.info('cpunode reflector address: %s, %s' % (refaddress, refport))
            temp = j.atyourservice.new(name='autossh', instance=instance, args=data_autossh, parent=node)
            temp.consume('node', node.instance)
            temp.install(deps=True)

        else:
            autossh = False
            j.console.warning('reflector not found, skipping autossh')
        return autossh

    def initVnasCloudSpace(self, gitlablogin, gitlabpasswd, delete=False):
        j.console.info("get secret key for cloud api")
        if self._spacesecret is None:
            j.events.inputerror_critical('no spacesecret set, need to call connect() method first')
        else:
            spacesecret = self._spacesecret

        j.console.info("check local ssh key exists")
        keypath = '/root/.ssh/id_rsa'
        if not j.system.fs.exists(path=keypath):
            j.console.info("generate local rsa key")
            j.system.platform.ubuntu.generateLocalSSHKeyPair()

        if self.actionCheck(spacesecret, "vnas_machinecreate") is False:
            # create ovc_git vm
            id, ip, port = self.api.createMachine(spacesecret, 'vnas_master', memsize='2', ssdsize='10',
                                                  imagename='ubuntu 14.04 x64', sshkey='/root/.ssh/id_rsa.pub', delete=delete)

            # portforward 22 to 22 on ovc_git
            self.api.createTcpPortForwardRule(spacesecret, 'vnas_master', 22, pubipport=1500)

            # ssh connetion to the vm
            cl = j.ssh.connect(ip, port, keypath=keypath, verbose=True)

            # generate key pair on the vm
            j.console.info('generate keypair on the vm')
            cl.ssh_keygen('root', 'rsa')

            self.actionDone(spacesecret, "vnas_machinecreate", (ip, port))
        else:
            ip, port = self.actionCheck(spacesecret, "vnas_machinecreate")
            cl = j.ssh.connect(ip, 22, keypath=keypath, verbose=True)

        if self.actionCheck(spacesecret, "vnas_jumpscale") is False:
            # install Jumpscale
            j.console.info("install jumpscale")
            cmd = j.do.getInstallCommand()
            cl.run(cmd)
            j.console.info("jumpscale installed")

            j.console.info("add openvcloud domain to atyourservice")
            content = """
metadata.openvcloud            =
    url:'https://github.com/0-complexity/openvcloud_ays',
"""
            cl.file_append('/opt/jumpscale7/hrd/system/atyourservice.hrd', content)
            self.actionDone(spacesecret, "vnas_jumpscale")

        if self.actionCheck(spacesecret, "vnas-gitcredentials") is False:
            cl.run('jsconfig hrdset -n whoami.git.login -v "%s"' % gitlablogin)
            cl.run('jsconfig hrdset -n whoami.git.passwd -v "%s"' % urllib.quote_plus(gitlabpasswd))
            self.actionDone(spacesecret, "vnas-gitcredentials")

        if self.actionCheck(spacesecret, "vnas_ovc_client") is False:
            # create ovc_client to save ovc connection info
            args = 'instance.param.location:%s instance.param.login:%s instance.param.passwd:%s instance.param.cloudspace:%s instance.param.apiurl:%s' % (
                self.location, self.login, self.passwd, self.cloudspace, self.apiURL)
            cl.run('ays install -n ovc_client --data "%s" -r' % args)
            self.actionDone(spacesecret, "vnas_ovc_client")

        ss = cl.host().split(':')
        ip, port = ss[0], ss[1]
        j.console.info("connect to the vnas_master with\nssh root@%s -p %s" % (ip, port))

    def vmExists(self, spacesecret, name):
        try:
            cl.api.getMachineObject(cl._spacesecret, 'vnas_master')
        except Exception as e:
            if e.message and e.message.find('Could not find machine') != -1:
                return False
        return True
