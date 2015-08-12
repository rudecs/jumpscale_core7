from JumpScale import j


class OpenvcloudFactory(object):
    def get(self, apiurl='www.mothership1.com'):
        return Openvlcoud(apiurl)


class Openvlcoud(object):
    def __init__(self, apiurl):
        self._spacesecret = None
        self.api = j.tools.ms1.get(apiurl)

    def _createGitRepo(self, addr, login, passwd, account, repoName):
        gitlab = j.clients.gitlab.get(addr=addr, login=login, passwd=passwd, instance='main')
        gitlab.create(account, repoName, public=False)

    def initMasterGitVM(self, login, passwd, location, cloudspace, gitlabUrl,
            gitlabLogin, gitlabPasswd, gitlabAccountname, gitlabReponame, recoverypasswd,delete=False):
        """

        master git machine is the machine which holds all the configuration for the master environment of an openvcloud

        example locations on mothership1:  ca1 (canada),us2 (us), eu2 (belgium), eu1 (uk)

        example:
        cl.initMasterGitVMovc("despiegk","????","eu2","BE","git.aydo.com",\
            gitlabLogin="despiegk",gitlabPasswd="????",\
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
        print "get secret key for cloud api"
        spacesecret = self.api.getCloudspaceSecret(login, passwd, cloudspace, location)

        print "check local ssh key exists"
        keypath='/root/.ssh/id_rsa'
        if not j.system.fs.exists(path=keypath):
            print "generate local rsa key"
            j.system.platform.ubuntu.generateLocalSSHKeyPair()

        if len(recoverypasswd)<8:
            j.events.inputerror_critical("Recovery passwd needs to be at least 8 chars")

        # create ovc_git vm
        id, ip, port = self.api.createMachine(spacesecret, 'ovc_git', memsize='0.5', ssdsize='10', imagename='ubuntu.14.04.x64',sshkey='/root/.ssh/id_rsa.pub',delete=delete)

        if not gitlabUrl.lower().startswith("https"):
            gitlabUrl = 'https://%s' % gitlabUrl

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

        # install Jumpscale
        print "install jumpscale"
        cl.run('curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh')
        print "jumpscale installed"

        # create new git repo
        print "create git repo"
        self._createGitRepo(gitlabUrl, gitlabLogin, gitlabPasswd, gitlabAccountname, gitlabReponame)

        # clone templates repo and change url
        gitlabPasswd = gitlabPasswd.replace('$', '\$')
        gitlabPasswd = gitlabPasswd.replace('@', '\@')
        repoURL = 'https://%s:%s@%s/%s/%s' % (gitlabLogin, gitlabPasswd, gitlabUrl, gitlabAccountname, gitlabReponame)
        cl.run('git clone https://git.aydo.com/openvcloudEnvironments/OVC_GIT_Tmpl.git /opt/ovc_git')
        cl.run('cd /opt/ovc_git; git remote set-url origin %s' % repoURL)

        # create ms1_client to save ms1 connection info
        args = 'param.location:%s param.login:%s param.passwd:%s param.cloudspace:%s' % (location, login, passwd, cloudspace)
        cl.run('ays install -n ms1_client --data "%s"' % args)
