from JumpScale import j
import json

class OpenvcloudFactory(object):
    def get(self, apiurl='www.mothership1.com'):
        return Openvlcoud(apiurl)


class Openvlcoud(object):
    def __init__(self, apiurl):
        self._spacesecret = None
        self.api = j.tools.ms1.get(apiurl)
        self.db=j.db.keyvaluestore.getFileSystemStore("aysgit")
        self.reset=False

    def connect(self, login, passwd, location,cloudspace,reset=False):
        """
        example locations on mothership1:  ca1 (canada),us2 (us), eu2 (belgium), eu1 (uk)
        @param reset if True then will not look at history
        """
        self.reset=reset
        self.login=login
        self.passwd=passwd
        self.location=location
        self.cloudspace=cloudspace
        self._spacesecret = self.api.getCloudspaceSecret(login, passwd, cloudspace, location)
        return self._spacesecret

    def actionCheck(self,gitlaburl,actionname):
        if self.reset:
            return False
        key="%s__%s"%(gitlaburl,actionname)
        if self.db.exists("",key):
            print "Action:%s done"%actionname
            return self.db.get("",key)
        return False

    def actionDone(self,gitlaburl,actionname,args=None):
        key="%s__%s"%(gitlaburl,actionname)
        self.db.set("",key,args)

    def initAYSGitVM(self, gitlaburl, gitlablogin,gitlabpasswd,recoverypasswd,delete=False):
        """

        gitlaburl example 
        https://git.aydo.com/openvcloudEnvironments/testkds.git
        #do not use login:passwd@ in the url

        master git machine is the machine which holds all the configuration for the master environment of an openvcloud

        example:
        cl.initMasterGitVMovc("despiegk","????","eu2","BE","git.aydo.com",\
            gitlablogin="despiegk",gitlabpasswd="????",\
            gitlabAccountname="test",gitlabReponame="testspace",recoverypasswd="9999")

        will do the following
        - init connection with openvcloud API
        - create machine which will host the git repo for this openvcloud env
        - do portforward from internet to git master for ssh (port 22)
        - create remote ssh key pair
        - secure the gitvm (give local user sshpair access)
        - install jumpscale
        - create the required repo on gitlab
        - push initial content
        - pull git repo onto the vmachine
        - create openvcloud connection ays on vmachine so that future connections to openvcloud can be made

        """

        #check gitlab repo exists or needs to be created
        # create new git repo
        print "create git repo"
        if gitlaburl.find("@")!=-1:
            j.events.inputerror_critical('do not use login:passwd@ in the url')
        if not gitlaburl.startswith("http"):
            gitlaburl="https://%s"%gitlaburl

        gitlabAccountname, gitlabReponame=j.clients.gitlab.getAccountnameReponameFromUrl(gitlaburl)        
        gitlaburl0="/".join(gitlaburl.split("/")[:3])      

        if self.actionCheck(gitlaburl,"gitcreate")==False:
            gitlab = j.clients.gitlab.get(gitlaburl0,gitlablogin,gitlabpasswd)
            gitlab.create(gitlabAccountname, gitlabReponame, public=False)      
            self.actionDone(gitlaburl,"gitcreate")  

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

        if len(recoverypasswd)<8:
            j.events.inputerror_critical("Recovery passwd needs to be at least 8 chars")

        if self.actionCheck(gitlaburl,"machinecreate")==False:
            # create ovc_git vm
            id, ip, port = self.api.createMachine(spacesecret, 'ovc_git', memsize='0.5', ssdsize='10', imagename='ubuntu.14.04.x64',sshkey='/root/.ssh/id_rsa.pub',delete=delete)


            # portforward 22 to 22 on ovc_git
            self.api.createTcpPortForwardRule(spacesecret, 'ovc_git', 22, pubipport=22)

            # ssh connetion to the vm
            cl = j.ssh.connect(ip, port,keypath=keypath,verbose=True)

            # generate key pair on the vm
            print 'generate keypair on the vm'
            cl.ssh_keygen('root', 'rsa')

            # secure vm and give access to the local machine
            u = j.ssh.unix.get(cl)
            u.secureSSH('', recoverypasswd=recoverypasswd)
            self.actionDone(gitlaburl,"machinecreate",(ip,port)) 
        else:
            ip,port=self.actionCheck(gitlaburl,"machinecreate")
            cl=j.ssh.connect(ip, 22,keypath=keypath,verbose=True)

        if self.actionCheck(gitlaburl,"jumpscale")==False:
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
            self.actionDone(gitlaburl,"jumpscale") 

        repopath="/opt/code/git/%s/%s/"%(gitlabAccountname,gitlabReponame)
        if True or self.actionCheck(gitlaburl,"gitlabclone")==False:
            # clone templates repo and change url
            gitlabpasswd = gitlabpasswd.replace('$', '\$')
            gitlabpasswd = gitlabpasswd.replace('@', '\@')
            repoURL = 'https://%s:%s@%s/%s/%s' % (gitlablogin, gitlabpasswd, gitlaburl, gitlabAccountname, gitlabReponame)
            cl.run('git clone https://git.aydo.com/openvcloudEnvironments/OVC_GIT_Tmpl.git %s'%repopath)
            cl.run('cd %s; git remote set-url origin %s' % (repopath,repoURL))
            self.actionDone(gitlaburl,"gitlabclone") 
    
        if self.actionCheck(gitlaburl,"gitcredentials")==False:
            cl.run('jsconfig hrdset -n whoami.git.login -v %s'%gitlablogin)
            cl.run('jsconfig hrdset -n whoami.git.passwd -v %s'%gitlabpasswd)
            self.actionDone(gitlaburl,"gitcredentials") 

        if self.actionCheck(gitlaburl,"ms1client")==False:
            # create ms1_client to save ms1 connection info
            args = 'param.location:%s param.login:%s param.passwd:%s param.cloudspace:%s' % (self.location, self.login, self.passwd, self.cloudspace)
            cl.run('ays install -n ms1_client --data "%s"' % args)
            self.actionDone(gitlaburl,"ms1client")

        if True or self.actionCheck(gitlaburl,"rememberssh")==False:
            # create ms1_client to save ms1 connection info
            args = 'param.recovery.passwd:%s param.ip:%s' % (recoverypasswd, ip)
            cl.run('ays install -n git_vm --data "%s"' % args)
            cl.run('cd %s;jscode push'%repopath)
            self.actionDone(gitlaburl,"rememberssh")

    def connectAYSGitVM(self, gitlaburl, gitlablogin,gitlabpasswd):
        keypath='/root/.ssh/id_rsa'
        if self.actionCheck(gitlaburl,"machinecreate")!=False:
            #means on this machien we have alrady created the machine so we have the credentials
            ip,port=self.actionCheck(gitlaburl,"machinecreate")
            cl=j.ssh.connect(ip, 22,keypath=keypath,verbose=True)
        else:
            from IPython import embed
            print "DEBUG NOW ooo"
            embed()
            

        if self.actionCheck(gitlaburl,"gitcredentials")!=False:
            cl.run('jsconfig hrdset -n whoami.git.login -v %s'%gitlablogin)
            cl.run('jsconfig hrdset -n whoami.git.passwd -v %s'%gitlabpasswd)


        cl.run('ays mdupdate')

        cl.fabric.api.open_shell()


    def initReflectorVM(self,  passphrase, delete=False):
        """
        this methods need to be run from the ovc_git VM

        Master reflector VM is the machine that received the reverse tunnel from the nodes and create connection betwee master cloudspace and nodes

        will do following:
            - create vmachine
            - install JumpScale
            - install ovc_reflector service, this service do:
                - create keypair with passphrase for root
                - create user guest
                - create keypair for guest
            - copy keys from root and guest and copy the into the keys folder of the ovc_git repo
        """

        print "get secret key for cloud api"
        if self._spacesecret is None:
            j.events.inputerror_critical('no spacesecret set, need to call connect() method first')
        else:
            spacesecret = self._spacesecret

        # create ovc_git vm
        self.api.createMachine(spacesecret, 'ovc_reflector', memsize='0.5', ssdsize='10', imagename='ubuntu.14.04.x64',sshkey='/root/.ssh/id_rsa.pub',delete=delete)
        machine = self.api.getMachineObject(spacesecret, 'ovc_reflector')
        ip = machine['interfaces'][0]['ipAddress']

        cl = j.ssh.connect(ip, 22, keypath='/root/.ssh/id_rsa')

        # install Jumpscale
        print "install jumpscale"
        cl.run('curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh')
        print "jumpscale installed"

        # create service required to connect to ovc reflector with ays
        data = {
            'instance.key.priv': j.system.fs.fileGetContents('/root/.ssh/id_rsa')
        }
        keyService = j.atyourservice.new(name='sshkey', instance='ovc_reflector', args=data)
        keyService.install()

        data = {
            'instance.ip': ip,
            'instance.ssh.port': 22,
            'instance.login': 'root',
            'instance.password': '',
            'instance.sshkey': keyService.instance,
            'instance.jumpscale': False,
            'instance.ssh.shell': '/bin/bash -l -c'
        }
        j.atyourservice.remove(name='node.ssh', instance='ovc_reflector')
        nodeService = j.atyourservice.new(name='node.ssh', instance='ovc_reflector', args=data)
        nodeService.install(reinstall=True)

        data = {
            'instance.root.passphrase': passphrase,
        }
        reflectorService = j.atyourservice.new(name='ovc_reflector', parent=nodeService, args=data)
        reflectorService.consume('node', nodeService.instance)
        reflectorService.install(reinstall=True)

        keys = {
            '/root/.ssh/id_rsa': '/opt/ovc_git/keys/reflector_root',
            '/root/.ssh/id_rsa.pub': '/opt/ovc_git/keys/reflector_root.pub',
            '/home/guest/.ssh/id_rsa': '/opt/ovc_git/keys/reflector_guest',
            '/home/guest/.ssh/id_rsa.pub': '/opt/ovc_git/keys/reflector_guest.pub'
        }
        for source, destination in keys.iteritems():
            content = cl.file_read(source)
            j.system.fs.writeFile(filename=destination, contents=content)

    def initProxyVM(self, host, dcpmServerName, dcpmInternalHost, ovsServerName, defenseServerName, novncServerName,
        delete=False):
        """
        this methods need to be run from the ovc_git VM

        Master reflector VM is the machine that received the reverse tunnel from the nodes and create connection betwee master cloudspace and nodes

        will do following:
            - create vmachine
            - create portforward on port 80 and 443
            - install JumpScale
            - install ssloffloader service
        """

        print "get secret key for cloud api"
        if self._spacesecret is None:
            j.events.inputerror_critical('no spacesecret set, need to call connect() method first')
        else:
            spacesecret = self._spacesecret

        # create ovc_git vm
        self.api.createMachine(spacesecret, 'ovc_proxy', memsize='0.5', ssdsize='10', imagename='ubuntu.14.04.x64',sshkey='/root/.ssh/id_rsa.pub',delete=delete)
        machine = self.api.getMachineObject(spacesecret, 'ovc_reflector')
        ip = machine['interfaces'][0]['ipAddress']

        # portforward 80 and 443 to 80 and 442 on ovc_proxy
        self.api.createTcpPortForwardRule(spacesecret, 'ovc_proxy', 80, pubipport=80)
        self.api.createTcpPortForwardRule(spacesecret, 'ovc_proxy', 443, pubipport=443)

        cl = j.ssh.connect(ip, 22, keypath='/root/.ssh/id_rsa')

        # install Jumpscale
        print "install jumpscale"
        cl.run('curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh')
        print "jumpscale installed"

        # create service required to connect to ovc reflector with ays
        data = {
            'instance.key.priv': j.system.fs.fileGetContents('/root/.ssh/id_rsa')
        }
        keyService = j.atyourservice.new(name='sshkey', instance='ovc_proxy', args=data)
        keyService.install()

        data = {
            'instance.ip': ip,
            'instance.ssh.port': 22,
            'instance.login': 'root',
            'instance.password': '',
            'instance.sshkey': keyService.instance,
            'instance.jumpscale': False,
            'instance.ssh.shell': '/bin/bash -l -c'
        }
        j.atyourservice.remove(name='node.ssh', instance='ovc_proxy')
        nodeService = j.atyourservice.new(name='node.ssh', instance='ovc_proxy', args=data)
        nodeService.install(reinstall=True)

        cloudspaceObj = self.api.getCloudspaceObj(spacesecret)
        data = {
            'instance.host': host,
            'instance.master.ipadress': cloudspaceObj['publicipaddress'],
            'instance.dcpm.servername': dcpmServerName,
            'instance.dcpm.internalhost': dcpmInternalHost,
            'instance.ovs.servername': ovsServerName,
            'instance.defense.servername': defenseServerName,
            'instance.novnc.servername': novncServerName
        }
        ssloffloader = j.atyourservice.new(name='ssloffloader', args=data, parent=nodeService)
        ssloffloader.consume('node', nodeService.instance)
        ssloffloader.install(reinstall=True, deps=True)

    def initMasterVM(self, masterPasswd, publicipStart, publicipEnd, dcpmUrl, ovsUrl, portalUrl, oauthUrl, defenseUrl, delete=False):
        """
        this methods need to be run from the ovc_git VM

        Master reflector VM is the machine that received the reverse tunnel from the nodes and create connection betwee master cloudspace and nodes

        will do following:
            - create vmachine
            - install JumpScale
            - create keypair for root
            - copy keypair in ovc_git keys directory
            - install cb_master_aio service
            - put reflector_guest.pub in /root/.ssh/authorized_keys
        """

        print "get secret key for cloud api"
        if self._spacesecret is None:
            j.events.inputerror_critical('no spacesecret set, need to call connect() method first')
        else:
            spacesecret = self._spacesecret

        # create ovc_git vm
        self.api.createMachine(spacesecret, 'ovc_master', memsize='4', ssdsize='40', imagename='ubuntu.14.04.x64',sshkey='/root/.ssh/id_rsa.pub',delete=delete)
        machine = self.api.getMachineObject(spacesecret, 'ovc_master')
        ip = machine['interfaces'][0]['ipAddress']

        # portforward 4444 to 4444 ovc_master
        self.api.createTcpPortForwardRule(spacesecret, 'ovc_proxy', 4444, pubipport=4444)

        cl = j.ssh.connect(ip, 22, keypath='/root/.ssh/id_rsa')

        # generate key pair on the vm
        print 'generate keypair on the vm'
        cl.ssh_keygen('root', keytype='rsa')
        keys = {
            '/root/.ssh/id_rsa': '/opt/ovc_git/master_root',
            '/root/.ssh/id_rsa.pub': '/opt/ovc_git/master_root.pub',
        }
        for source, destination in keys.iteritems():
            content = cl.file_read('/root/.ssh/id_rsa')
            j.system.fs.writeFile(filename='/opt/ovc_git/master_root', contents=content)

        # install Jumpscale
        print "install jumpscale"
        cl.run('curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh')
        print "jumpscale installed"

        # create service required to connect to ovc reflector with ays
        data = {
            'instance.key.priv': j.system.fs.fileGetContents('/root/.ssh/id_rsa')
        }
        keyService = j.atyourservice.new(name='sshkey', instance='ovc_master', args=data)
        keyService.install()

        data = {
            'instance.ip': ip,
            'instance.ssh.port': 22,
            'instance.login': 'root',
            'instance.password': '',
            'instance.sshkey': keyService.instance,
            'instance.jumpscale': False,
            'instance.ssh.shell': '/bin/bash -l -c'
        }
        j.atyourservice.remove(name='node.ssh', instance='ovc_master')
        nodeService = j.atyourservice.new(name='node.ssh', instance='ovc_master', args=data)
        nodeService.install(reinstall=True)

        cloudspaceObj = self.api.getCloudspaceObj(spacesecret)
        data = {
            'instance.param.rootpasswd': masterPasswd,
            'instance.param.publicip.gateway': cloudspaceObj['publicipaddress'],
            'instance.param.publicip.netmask': '255.255.255.0',
            'instance.param.publicip.start': publicipStart,
            'instance.param.publicip.end': publicipEnd,
            'instance.param.dcpm.url': dcpmUrl,
            'instance.param.ovs.url': ovsUrl,
            'instance.param.portal.url': portalUrl,
            'instance.param.oauth.url': oauthUrl,
            'instance.param.defense.url': defenseUrl
        }
        master = j.atyourservice.new(name='cb_master_aio', args=data, parent=nodeService)
        master.consume('node', nodeService.instance)
        master.install(reinstall=True, deps=True)

        content = j.system.fs.fileGetContents('/opt/ovc_git/reflector_guest.pub')
        cl.file_append('/root/.ssh/.ssh/authorized_keys', content)
