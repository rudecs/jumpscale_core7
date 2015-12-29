from JumpScale import j
import json
import urllib
import time

class OpenvcloudFactory(object):
    def get(self):
        return Openvclcoud()

class Openvclcoud(object):
    def __init__(self):
        self.reset = False
        self.db = j.db.keyvaluestore.getFileSystemStore("aysgit")
        
        self._ms1 = {}
        self._docker = {}
        self.bootstrapPort = '5000'
    
    def initLocalhost(self, gitlaburl, gitlablogin, gitlabpasswd):
        self.preprocess()
        
        print "[+] creating git repository"

        if gitlaburl.find("@") != -1:
            j.events.inputerror_critical('[-] do not use "login:passwd@" in the url')

        if not gitlaburl.startswith("http"):
            gitlaburl = "https://%s" % gitlaburl

        gitlabAccountname, gitlabReponame = j.clients.gitlab.getAccountnameReponameFromUrl(gitlaburl)
        gitlaburl0 = "/".join(gitlaburl.split("/")[:3])

        print '[+] git group: %s' % gitlabAccountname
        print '[+] environment: %s' % gitlabReponame

        gitlab = j.clients.gitlab.get(gitlaburl0, gitlablogin, gitlabpasswd)
        
        print '[+] checking for existing project'
        
        projects = gitlab.getProjects()
        for project in projects:
            if project['name'] == gitlabReponame and project['namespace']['name'] == gitlabAccountname:
                print '[-] %s/%s: project already exists' % (gitlabAccountname, gitlabReponame)
                print '[-] if you removed it shortly, this is probably related to cache, please wait'
                j.application.stop()

    def initMothership(self, login, passwd, location, cloudspace, reset=False, apiurl='www.mothership1.com'):
        print '[+] building mothership1 based environment'
        
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
        print '[+] building docker based environment'
        
        print '[+] building the base image'
        today = time.strftime('%Y-%m-%d')
        image = 'openvcloud/%s' % today
        
        args = {'instance.image.name': image}
        service = j.atyourservice.new(name='docker_ovc', args=args)
        service.install(reinstall=True)
        
        self._docker = {
            'remote': host,
            'port': port,
            'public': public,
            'image': image
        }
        
        vm = j.clients.vm.get('docker', self._docker)
        
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
        print "[+] checking local ssh key"
        
        keypath = '/root/.ssh/id_rsa'
        
        if not j.system.fs.exists(path=keypath):
            print "[+] generating local rsa key"
            j.system.platform.ubuntu.generateLocalSSHKeyPair()
        
        print '[+] checking for redis'
        if not j.system.net.tcpPortConnectionTest("localhost", 9999, timeout=None):
            redis = j.atyourservice.findServices(instance='system', name='redis')
            
            if len(redis) == 0:
                print '[-] cannot continue, redis is not installed'
                j.application.stop()
                
            redis[0].start()

    def actionCheck(self,gitlaburl,actionname):
        if self.reset:
            return False

        key = "%s__%s" % (gitlaburl, actionname)

        if self.db.exists("", key):
            print "[-] action: %s already done" % actionname
            return self.db.get("", key)

        return False

    def actionDone(self,gitlaburl,actionname,args=None):
        key = "%s__%s" % (gitlaburl, actionname)
        self.db.set("", key, args)
    
    def jumpscale(self, remote):
        if remote.file_exists('/opt/jumpscale7/'):
            print "[+] jumpscale seems already installed, skipping"
            return
        
        print "[+] installing jumpscale"
        remote.run('curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh')

    def initAYSGitVM(self, machine, gitlaburl, gitlablogin, gitlabpasswd, recoverypasswd, domain, delete=False):
        keypath = '/root/.ssh/id_rsa'

        if len(recoverypasswd) < 6:
            j.events.inputerror_critical("[-] recovery passwd needs to be at least 6 chars")
        
        print '[+] creating gitlab project'
        
        gitlabAccountname, gitlabReponame = j.clients.gitlab.getAccountnameReponameFromUrl(gitlaburl)
        gitlaburl0 = "/".join(gitlaburl.split("/")[:3])
        
        gitlab = j.clients.gitlab.get(gitlaburl0, gitlablogin, gitlabpasswd)
        gitlab.createProject(gitlabAccountname, gitlabReponame, public=False)

        cl = j.ssh.connect(machine['remote'], machine['port'], keypath=keypath, verbose=True)

        print '[+] generating keypair on the vm'
        cl.ssh_keygen('root', 'rsa')

        if self.actionCheck(gitlaburl, "jumpscale") is False:
            # install jumpscale
            self.jumpscale(cl)

            print "[+] adding openvcloud domain to atyourservice"
            content  = "metadata.openvcloud            =\n"
            content += "    branch:'2.0',\n"
            content += "    url:'https://git.aydo.com/0-complexity/openvcloud_ays',\n"

            cl.file_append('/opt/jumpscale7/hrd/system/atyourservice.hrd', content)
            self.actionDone(gitlaburl, "jumpscale")

        if self.actionCheck(gitlaburl, "gitcredentials") is False:
            cl.run('jsconfig hrdset -n whoami.git.login -v "ssh"')
            cl.run('jsconfig hrdset -n whoami.git.passwd -v "ssh"')
            infos = gitlab.getUserInfo(gitlablogin)

            email = infos['email'] if infos.has_key('email') else 'nobody@aydo.com'
            name = infos['name'] if infos['name'] != '' else gitlablogin

            cl.run('git config --global user.email "%s"' % email)
            cl.run('git config --global user.name "%s"' % name)
            self.actionDone(gitlaburl, "gitcredentials")
            
            allowhosts = ["github.com", "git.aydo.com"]
            
            for host in allowhosts:
                cl.run('echo "Host %s" >> /root/.ssh/config' % host)
                cl.run('echo "    StrictHostKeyChecking no" >> /root/.ssh/config')
                cl.run('echo "" >> /root/.ssh/config')

        repopath = "/opt/code/git/%s/%s/" % (gitlabAccountname, gitlabReponame)

        if self.actionCheck(gitlaburl, "gitlabclone") is False:
            repoURL = 'git@git.aydo.com:%s/%s.git' % (gitlabAccountname, gitlabReponame)

            if not cl.file_exists(repopath):
                host = 'git@git.aydo.com'
                
                cl.run('git clone %s:openvcloudEnvironments/OVC_GIT_Tmpl.git %s' % (host, repopath))
                cl.run('cd %s; git remote set-url origin %s' % (repopath, repoURL))

                # Note: rebase prevents for asking to merge local tree with remote
                cl.run('cd %s; git pull --rebase' % repopath)

            self.actionDone(gitlaburl, "gitlabclone")
        
        if self.actionCheck(gitlaburl, 'copyKeys') is False:
            keys = {
                '/root/.ssh/id_rsa': (j.system.fs.joinPaths(repopath, 'keys', 'git_root'), ),
                # '/root/.ssh/id_rsa.pub': (j.system.fs.joinPaths(repopath, 'keys', 'git_root.pub'), '/root/.ssh/authorized_keys'),
                '/root/.ssh/id_rsa.pub': (j.system.fs.joinPaths(repopath, 'keys', 'git_root.pub'), ),
            }

            for source, dests in keys.iteritems():
                content = cl.file_read(source)
                for dest in dests:
                    cl.file_write(dest, content)
                    cl.run('chmod 600 %s' % dest)

            # append key to authorized hosts
            cl.run("cat %s >> /root/.ssh/authorized_keys" % keys['/root/.ssh/id_rsa.pub'])
            
            self.actionDone(gitlaburl, 'copyKeys')

        # saving clients
        if machine['type'] == 'ms1':
            # create ms1_client to save ms1 connection info
            args  = 'instance.param.location:%s ' % self._ms1['location']
            args += 'instance.param.login:%s ' % self._ms1['username']
            args += 'instance.param.passwd:%s ' % self._ms1['password']
            args += 'instance.param.cloudspace:%s' % self._ms1['cloudspace']
            
            cl.run('cd %s; ays install -n ms1_client --data "%s" -r' % (repopath, args))
        
        if machine['type'] == 'docker':
            # create ms1_client to save ms1 connection info
            args  = 'instance.remote.host:%s ' % self._docker['remote']
            args += 'instance.remote.port:%s ' % self._docker['port']
            args += 'instance.public.address:%s ' % self._docker['public']
            args += 'instance.image.base:%s' % machine['image']
            
            cl.run('cd %s; ays install -n docker_client --data "%s" -r' % (repopath, args))
        
        # ensure that portal libs are installed
        cl.run('cd %s; ays install -n portal_lib -r' % (repopath))
        
        
        
        # create ovc_setup instance to save settings
        args  = 'instance.ovc.environment:%s ' % gitlabReponame
        args += 'instance.ovc.path:/opt/code/git/%s/%s ' % (gitlabAccountname, gitlabReponame)
        args += 'instance.ovc.ms1.instance:main '           # FIXME, remove me
        args += 'instance.ovc.gitlab_client.instance:main ' # FIXME, remove me
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
        
        # ensure that ssh agent is running and add the new key
        j.do.execute('eval $(ssh-agent -s)')
        
        print ''
        print '[+] environment is ready to be deployed'
        print '[+] you can now ssh the ovcgit host to configure the environment'
        print '[+]   ssh root@%s -p %s -A' % (machine['remote'], machine['port'])

    def initVnasCloudSpace(self, gitlablogin, gitlabpasswd, delete=False):
        print "get secret key for cloud api"
        if self._spacesecret is None:
            j.events.inputerror_critical('no spacesecret set, need to call connect() method first')
        else:
            spacesecret = self._spacesecret

        print "check local ssh key exists"
        keypath='/root/.ssh/id_rsa'
        if not j.system.fs.exists(path=keypath):
            print "generate local rsa key"
            j.system.platform.ubuntu.generateLocalSSHKeyPair()

        if self.actionCheck(spacesecret, "vnas_machinecreate") is False:
            # create ovc_git vm
            id, ip, port = self.api.createMachine(spacesecret, 'vnas_master', memsize='2', ssdsize='10', imagename='ubuntu 14.04 x64',sshkey='/root/.ssh/id_rsa.pub',delete=delete)

            # portforward 22 to 22 on ovc_git
            self.api.createTcpPortForwardRule(spacesecret, 'vnas_master', 22, pubipport=1500)

            # ssh connetion to the vm
            cl = j.ssh.connect(ip, port, keypath=keypath, verbose=True)

            # generate key pair on the vm
            print 'generate keypair on the vm'
            cl.ssh_keygen('root', 'rsa')

            self.actionDone(spacesecret, "vnas_machinecreate", (ip, port))
        else:
            ip, port = self.actionCheck(spacesecret, "vnas_machinecreate")
            cl = j.ssh.connect(ip, 22, keypath=keypath, verbose=True)

        if self.actionCheck(spacesecret, "vnas_jumpscale") is False:
            # install Jumpscale
            print "install jumpscale"
            cl.run('curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh')
            print "jumpscale installed"

            print "add openvcloud domain to atyourservice"
            content = """
metadata.openvcloud            =
    url:'https://git.aydo.com/0-complexity/openvcloud_ays',
"""
            cl.file_append('/opt/jumpscale7/hrd/system/atyourservice.hrd', content)
            self.actionDone(spacesecret, "vnas_jumpscale")

        if self.actionCheck(spacesecret, "vnas-gitcredentials") is False:
            cl.run('jsconfig hrdset -n whoami.git.login -v "%s"' % gitlablogin)
            cl.run('jsconfig hrdset -n whoami.git.passwd -v "%s"' % urllib.quote_plus(gitlabpasswd))
            self.actionDone(spacesecret, "vnas-gitcredentials")

        if self.actionCheck(spacesecret, "vnas_ovc_client") is False:
            # create ovc_client to save ovc connection info
            args = 'instance.param.location:%s instance.param.login:%s instance.param.passwd:%s instance.param.cloudspace:%s instance.param.apiurl:%s' % (self.location, self.login, self.passwd, self.cloudspace, self.apiURL)
            cl.run('ays install -n ovc_client --data "%s" -r' % args)
            self.actionDone(spacesecret, "vnas_ovc_client")

        ss = cl.host().split(':')
        ip, port = ss[0], ss[1]
        print "connect to the vnas_master with\nssh root@%s -p %s" % (ip, port)

    def vmExists(self, spacesecret, name):
        try:
            cl.api.getMachineObject(cl._spacesecret, 'vnas_master')
        except Exception as e:
            if e.message and e.message.find('Could not find machine') != -1:
                return False
        return True
