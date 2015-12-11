from JumpScale import j

ActionsBase=j.atyourservice.getActionsBaseClass()

class ActionsBaseNode(ActionsBase):
    """Base Classe for all nodes services"""

    def execute(self, serviceObj, cmd):
        """
        execute the command `cmd` on the node
        and return the output of the command

        @rvalue string - output of cmd
        """
        cl = self.getSSHClient(serviceObj)
        return cl.sudo(cmd)

    def upload(self, serviceObj, source, dest):
        privKey, _ = self.getSSHKey(serviceObj)

        ip = serviceObj.hrd.get("instance.ip")
        port = serviceObj.hrd.get("instance.ssh.port")
        rdest = "%s:%s" % (ip, dest)

        login = serviceObj.hrd.get('instance.login', default='') or None
        if login:
            cl = self.getSSHClient(serviceObj)
            chowndir = dest
            while not cl.file_exists(chowndir):
                chowndir = j.system.fs.getParent(chowndir)
            cl.sudo("chown -R %s %s" % (login, chowndir))

        services = j.system.fs.walk(j.system.fs.getParent(source), pattern='*__*__*', return_folders=1, return_files=0)
        self._rsync(services, rdest, privKey, port, login)

    def download(self, serviceObj, source, dest):
        privKey, _ = self.getSSHKey(serviceObj)

        ip = serviceObj.hrd.get("instance.ip")
        port = serviceObj.hrd.get("instance.ssh.port")

        rsource = "%s:%s" % (ip, source)
        login = serviceObj.hrd.get('instance.login', default='') or None
        self._rsync([rsource], dest, privKey, port, login)

    def getSSHClient(self, serviceObj):
        """
        @rvalue ssh client object connected to the node
        """
        c = j.remote.cuisine

        ip = serviceObj.hrd.get('instance.ip')
        port = serviceObj.hrd.getInt('instance.ssh.port')
        login = serviceObj.hrd.get('instance.login', default='') or None
        password = serviceObj.hrd.get('instance.password', default='') or None
        privKey, _ = self.getSSHKey(serviceObj)

        if privKey:
            c.fabric.env["key"] = privKey
        if login and login != '':
            c.fabric.env['user'] = login
        c.fabric.env['shell'] = serviceObj.hrd.get('instance.ssh.shell', "/bin/bash -l -c")
        c.fabric.env['forward_agent'] = True
        c.fabric.env['sudo_prefix'] = "sudo -S -E -p '%(sudo_prompt)s' "

        if (password == "" or password is None) and privKey is None:
            raise RuntimeError(
                "can't connect to the node, should provide or password or a key to connect")
        if password:
            connection = c.connect(ip, port, passwd=password, login=login)
        else:
            connection = c.connect(ip, port, login=login)

        return connection

    def getSSHKey(self, serviceObj):
        """
        @rvalue tuple containing private and public key (priv, pub)
        """
        keyname = serviceObj.hrd.get("instance.sshkey")
        if keyname != "":
            sshkeyHRD = j.application.getAppInstanceHRD("sshkey", keyname, parent="")
            return (sshkeyHRD.get("instance.key.priv"), sshkeyHRD.get("instance.key.pub"))
        else:
            return (None, None)

    def installJumpscale(self, serviceObj):
        cl = self.getSSHClient(serviceObj)
        def extra():
            cl.package_ensure('curl', update=True)
        j.actions.start(name="extra", description='extra', action=extra,
                        stdOutput=True, serviceObj=serviceObj)

        def jumpscale():
            cl.sudo("curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh")
        j.actions.start(name="jumpscale", description='install jumpscale',
                        action=jumpscale,
                        stdOutput=True, serviceObj=serviceObj)

    def _rsync(self, sources, dest, key, port=22, login=None):
        """
        helper method that can be used by services implementation for
        upload/download actions
        """
        def generateUniq(name):
            import time
            epoch = int(time.time())
            return "%s__%s" % (epoch, name)

        sourcelist = list()
        if dest.find(":") != -1:
            # it's an upload
            dest = dest if dest.endswith("/") else dest + "/"
            sourcelist = [source.rstrip("/") for source in sources if j.do.isDir(source)]
        else:
            # it's a download
            if j.do.isDir(dest):
                dest = dest if dest.endswith("/") else dest + "/"
            sourcelist = [source.rstrip("/") for source in sources if source.find(":") != -1]

        source = ' '.join(sourcelist)

        keyloc = "/tmp/%s" % generateUniq('key')
        j.system.fs.writeFile(keyloc, key)
        j.system.fs.chmod(keyloc, 0o600)

        login = login or 'root'
        ssh = "-e 'ssh -o StrictHostKeyChecking=no -i %s -p %s -l %s'" % (
            keyloc, port, login)

        destPath = dest
        if dest.find(":") != -1:
            destPath = dest.split(':')[1]

        verbose = "-q"
        if j.application.debug:
            print("copy from\n%s\nto\n %s" % (source, dest))
            verbose = "-v"
        cmd = "rsync -a -u --exclude \"*.pyc\" --rsync-path=\"mkdir -p %s && rsync\" %s %s %s %s" % (
            destPath, verbose, ssh, source, dest)
        if j.application.debug:
            print cmd
        j.do.execute(cmd)
        j.system.fs.remove(keyloc)