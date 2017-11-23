from JumpScale import j
from collections import namedtuple

Package = namedtuple('Package', 'name version arch')


def getUbuntu():
    import lsb_release
    release = lsb_release.get_distro_information()['RELEASE']
    if release.startswith("14"):
        return Ubuntu()
    elif release.startswith('16'):
        return UbuntuSystemd()
    raise NotImplemented("Ubuntu version %s is not supported" % release)


class Ubuntu(object):

    def __init__(self):
        self._aptupdated = False
        self._checked = False
        self._cache = None
        self._version = "14"
        self.installedPackageNames = []

    def initApt(self):
        try:
            import apt
        except ImportError:
            # we dont wont jshell to break, self.check will take of this
            return
        apt.apt_pkg.init()
        if hasattr(apt.apt_pkg, 'Config'):
            cfg = apt.apt_pkg.Config
        else:
            cfg = apt.apt_pkg.Configuration
        try:
            cfg.set("APT::Install-Recommends", "0")
            cfg.set("APT::Install-Suggests", "0")
        except:
            pass
        self._cache = apt.Cache()
        self.aptCache = self._cache
        self.apt = apt

    def check(self, die=True):
        """
        check if ubuntu or mint (which is based on ubuntu)
        """
        if not self._checked:
            try:
                import lsb_release
                info = lsb_release.get_distro_information()['ID']
                release = lsb_release.get_distro_information()['RELEASE']
                if info != 'Ubuntu' and info != 'LinuxMint':
                    raise RuntimeError("Only ubuntu or mint supported.")
                if not release.startswith(self._version):
                    raise RuntimeError("Only ubuntu version 14.04 supported")
                self._checked = True
            except ImportError:
                self._checked = False
                if die:
                    raise RuntimeError("Only ubuntu or mint supported.")
        return self._checked

    def getVersion(self):
        """
        returns codename,descr,id,release
        known ids" raring, linuxmint
        """
        self.check()
        import lsb_release
        result = lsb_release.get_distro_information()
        return result["CODENAME"].lower().strip(), result["DESCRIPTION"], result["ID"].lower().strip(), result["RELEASE"],

    def existsUser(self, name):
        cmd = "getent passwd %s" % name
        rc, out = j.system.process.execute(cmd, dieOnNonZeroExitCode=False,
                                           outputToStdout=False, useShell=False, ignoreErrorOutput=True)
        if rc == 2:
            return False
        return True

    def existsGroup(self, name):
        cmd = "id -g %s" % name
        rc, out = j.system.process.execute(cmd, dieOnNonZeroExitCode=False,
                                           outputToStdout=False, useShell=False, ignoreErrorOutput=True)
        if rc == 1:
            return False
        return True

    def createUser(self, name, passwd, home=None, creategroup=True, deletefirst=False):
        # quietly add a user without password

        if deletefirst:
            cmd = 'deluser %s' % (name)
            j.do.execute(cmd, outputStdout=False, outputStderr=False, dieOnNonZeroExitCode=False)

        if self.existsUser(name) is False:
            cmd = 'adduser --quiet --disabled-password -shell /bin/bash --home /home/%s --gecos "User" %s' % (
                name, name)
            j.do.execute(cmd)

        # set password
        if passwd != '' or passwd is not None:
            cmd = 'echo "%s:%s" | chpasswd' % (name, passwd)
            j.do.execute(cmd)

        if creategroup and not self.existsGroup(name):
            self.createGroup(name)
            self.addUser2Group(name, name)

        # import JumpScale.baselib.remote.cuisine
        # c=j.remote.cuisine.api

        # if home==None:
        #     homeexists=True
        # else:
        #     homeexists=j.system.fs.exists(home)

        # c.user_ensure(name, passwd=passwd, home=home, uid=None, gid=None, shell=None, fullname=None, encrypted_passwd=False)
        # if creategroup:
        #     self.createGroup(name)
        #     self.addUser2Group(name,name)

        # if home!=None and not homeexists:
        #     c.dir_ensure(home,owner=name,group=name)

    def createGroup(self, groupname):
        cmd = 'groupadd  %s' % groupname
        j.do.execute(cmd)
        # import JumpScale.baselib.remote.cuisine
        # c=j.remote.cuisine.api
        # c.group_ensure(name)

    def addUser2Group(self, group, user):
        cmd = 'usermod -aG %s %s' % (group, user)
        j.do.execute(cmd)
        # import JumpScale.baselib.remote.cuisine
        # c=j.remote.cuisine.api
        # c.group_user_ensure(group, user)

    def checkInstall(self, packagenames, cmdname):
        """
        @param packagenames is name or array of names of ubuntu package to install e.g. curl
        @param cmdname is cmd to check e.g. curl
        """
        self.check()
        if j.basetype.list.check(packagenames):
            for packagename in packagenames:
                self.checkInstall(packagename, cmdname)
        else:
            packagename = packagenames
            result, out = j.system.process.execute("which %s" % cmdname, False)
            if result != 0:
                self.install(packagename)
            else:
                return
            result, out = j.system.process.execute("which %s" % cmdname, False)
            if result != 0:
                raise RuntimeError("Could not install package %s and check for command %s." % (packagename, cmdname))

    def install(self, packagename):

        cmd = 'unset JSBASE;unset PYTHONPATH;apt-get install %s --force-yes -y' % packagename
        j.system.process.executeWithoutPipe(cmd)

    def installVersion(self, packageName, version):
        '''
        Installs a specific version of an ubuntu package.

        @param packageName: name of the package
        @type packageName: str

        @param version: version of the package
        @type version: str
        '''

        self.check()
        if self._cache is None:
            self.initApt()

        mainPackage = self._cache[packageName]
        versionPackage = mainPackage.versions[version].package

        if not versionPackage.is_installed:
            versionPackage.mark_install()

        self._cache.commit()
        self._cache.clear()

    def installDebFile(self, path, installDeps=True):
        self.check()
        if self._cache is None:
            self.initApt()
        import apt.debfile
        deb = apt.debfile.DebPackage(path, cache=self._cache)
        if installDeps:
            deb.check()
            for missingpkg in deb.missing_deps:
                self.install(missingpkg)
        deb.install()

    def downloadInstallDebPkg(self, url, removeDownloaded=False, minspeed=20):
        """
        will download to tmp if not there yet
        will then install
        """
        j.do.chdir()  # will go to tmp
        path = j.do.download(url, "", overwrite=False, minspeed=minspeed, curl=True)
        self.installDebFile(path)
        if removeDownloaded:
            j.do.delete(path)

    def listFilesPkg(self, pkgname, regex=""):
        """
        list files of dpkg
        if regex used only output the ones who are matching regex
        """
        rc, out = j.system.process.execute("dpkg -L %s" % pkgname)
        if regex != "":
            return j.codetools.regex.findAll(regex, out)
        else:
            return out.split("\n")

    def remove(self, packagename):
        j.logger.log("ubuntu remove package:%s" % packagename, category="ubuntu.remove")
        self.check()
        if self._cache is None:
            self.initApt()
        pkg = self._cache[packagename]
        if pkg.is_installed:
            pkg.mark_delete()
        if packagename in self.installedPackageNames:
            self.installedPackageNames.pop(self.installedPackageNames.index(packagename))
        self._cache.commit()
        self._cache.clear()

    def serviceInstall(self, servicename, daemonpath, args='', respawn=True, pwd=None, env=None, reload=True):
        C = """
start on runlevel [2345]
stop on runlevel [016]
"""
        if respawn:
            C += "respawn\n"
        if pwd:
            C += "chdir %s\n" % pwd
        if env is not None:
            for key, value in list(env.items()):
                C += "env %s=%s\n" % (key, value)
        C += "exec %s %s\n" % (daemonpath, args)

        C = j.dirs.replaceTxtDirVars(C)

        j.system.fs.writeFile("/etc/init/%s.conf" % servicename, C)
        if reload:
            j.system.process.execute("initctl reload-configuration")

    def serviceUninstall(self, servicename):
        self.stopService(servicename)
        j.system.fs.remove("/etc/init/%s.conf" % servicename)

    def startService(self, servicename):
        # @todo P1 add log statements for all other methods of this class
        j.logger.log("start service on ubuntu for:%s" % servicename, category="ubuntu.start")
        if not self.statusService(servicename):
            cmd = "sudo start %s" % servicename
            # print cmd
            return j.system.process.execute(cmd)

    def stopService(self, servicename):
        cmd = "sudo stop %s" % servicename
        # print cmd
        return j.system.process.execute(cmd, False)

    def restartService(self, servicename):
        return j.system.process.execute("sudo restart %s" % servicename, False)

    def statusService(self, servicename):
        exitcode, output = j.system.process.execute("sudo status %s" % servicename, False)
        parts = output.split(' ')
        if len(parts) >= 2 and parts[1].startswith('start'):
            return True

        return False

    def serviceDisableStartAtBoot(self, servicename):
        j.system.process.execute("update-rc.d -f %s remove" % servicename)

    def serviceEnableStartAtBoot(self, servicename):
        j.system.process.execute("update-rc.d -f %s defaults" % servicename)

    def updatePackageMetadata(self, force=True):
        self.check()
        if self._cache is None:
            self.initApt()
        self._cache.update()

    def upgradePackages(self, force=True):
        self.check()
        if self._cache is None:
            self.initApt()
        self.updatePackageMetadata()
        self._cache.upgrade()

    def getPackageNamesRepo(self):
        return list(self._cache.keys())

    def getPackageNamesInstalled(self):
        if self.installedPackageNames == []:
            for key in self.getPackageNamesRepo():
                p = self._cache[key]
                if p.installed:
                    self.installedPackageNames.append(p.name)
        return self.installedPackageNames

    def getPackage(self, name):
        return self._cache[name]

    def findPackagesRepo(self, packagename):
        packagename = packagename.lower().strip().replace("_", "").replace("_", "")
        if self._cache is None:
            self.initApt()
        result = []
        for item in self.getPackageNamesRepo():
            item2 = item.replace("_", "").replace("_", "").lower()
            if item2.find(packagename) != -1:
                result.append(item)
        return result

    def findPackagesInstalled(self, packagename):
        packagename = packagename.lower().strip().replace("_", "").replace("_", "")
        if self._cache is None:
            self.initApt()
        result = []
        for item in self.getPackageNamesInstalled():
            item2 = item.replace("_", "").replace("_", "").lower()
            if item2.find(packagename) != -1:
                result.append(item)
        return result

    def getInstalledPackages(self):
        exitcode, result = j.system.process.execute('apt list --installed')
        packages = []
        for line in result.splitlines():
            meta = line.split()
            if len(meta) < 4:
                continue
            name = meta[0].split('/')[0]
            version = meta[1]
            arch = meta[2]
            packages.append(Package(name, version, arch))
        return packages

    def find1packageInstalled(self, packagename):
        j.logger.log("find 1 package in ubuntu", 6, category="ubuntu.find")
        res = self.findPackagesInstalled(packagename)
        if len(res) == 1:
            return res[0]
        elif len(res) > 1:
            raise RuntimeError("Found more than 1 package for %s" % packagename)
        raise RuntimeError("Could not find package %s" % packagename)

    def listSources(self):
        from aptsources import sourceslist
        return sourceslist.SourcesList()

    def changeSourceUri(self, newuri):
        src = self.listSources()
        for entry in src.list:
            entry.uri = newuri
        src.save()

    def listServices(self):
        exitcode, output = j.system.process.execute('initctl list')
        results = {}
        for line in output.splitlines():
            if line:
                parts = line.split()
                if len(parts) == 2:
                    key, value = parts
                    results[key] = 'enabled'
        return results

    def addSourceUri(self, url):
        url = url.replace(";", ":")
        name = url.replace("\\", "/").replace("http://", "").split("/")[0]
        path = "/etc/apt/sources.list.d/%s.list" % name
        j.do.writeFile(path, "deb %s\n" % url)

    def whoami(self):
        rc, result = j.system.process.execute("whoami")
        return result.strip()

    def checkroot(self):
        if self.whoami() != "root":
            j.events.inputerror_critical("only support root")

    def generateLocalSSHKeyPair(self, passphrase='', type="rsa", overwrite=False, path="/root/.ssh/id_rsa"):
        if overwrite and j.system.fs.exists(path=path):
            j.do.delete(path)
        if not j.system.fs.exists(path):
            if type not in ['rsa', 'dsa']:
                j.events.inputerror_critical("only support rsa or dsa for now")
            cmd = "ssh-keygen -t %s -b 4096 -P '%s' -f %s" % (type, passphrase, path)
            j.do.executeInteractive(cmd)


class UbuntuSystemd(Ubuntu):

    def __init__(self):
        super(UbuntuSystemd, self).__init__()
        self._version = "16"

    def serviceInstall(self, servicename, daemonpath, args='', respawn=True, pwd=None, env=None, reload=True):
        pwd = pwd or ''
        env = env or ''
        C = """\
[Unit]
Description={servicename}
Wants=network-online.target
After=network-online.target

[Service]
ExecStart={daemonpath} {args}
Restart=always
WorkingDirectory={pwd}
Environment={env}

[Install]
WantedBy=multi-user.target
                """.format(servicename=servicename, daemonpath=daemonpath, args=args, pwd=pwd, env=env)

        j.system.fs.writeFile("/etc/systemd/system/%s.service" % servicename, C)

        if reload:
            j.system.process.execute("systemctl daemon-reload;systemctl enable %s" % servicename)

    def serviceUninstall(self, servicename):
        self.stopService(servicename)
        filename = '%s.service'
        for file_ in j.system.fs.find('/etc/systemd/', filename):
            j.system.fs.remove(file_)

    def listServices(self):
        exitcode, output = j.system.process.execute('systemctl list-unit-files --no-pager --no-legend')
        results = {}
        for line in output.splitlines():
            if line:
                parts = line.split()
                if len(parts) == 2:
                    key, value = parts
                    results[key] = value
        return results

    def getServicePID(self, name):
        """
        returns the pid of the service
        if pid == 0, then there is no service running with this name
        """
        exitcode, output = j.system.process.execute("systemctl show -p MainPID {name}".format(name=name))
        pid = int(output.strip().split('=')[1])
        return pid

    def getPackageNamesInstalled(self):
        exitcode, result = j.system.process.execute('dpkg --get-selections')
        installedpackages = []
        for line in result.splitlines():
            packagename, status = line.split()
            if status != 'deinstall':
                installedpackages.append(packagename)
        return installedpackages

    def startService(self, servicename):
        # @todo P1 add log statements for all other methods of this class
        j.logger.log("start service on ubuntu for:%s" % servicename, category="ubuntu.start")
        if not self.statusService(servicename):
            cmd = "sudo systemctl start %s" % servicename
            # print cmd
            return j.system.process.execute(cmd)

    def stopService(self, servicename):
        cmd = "sudo systemctl stop %s" % servicename
        # print cmd
        return j.system.process.execute(cmd, False)

    def reloadService(self, servicename):
        cmd = "systemctl stop %s" % servicename
        # print cmd
        return j.system.process.execute(cmd, False)

    def serviceExists(self, servicename):
        for service in self.listServices():
            name, type_ = service.rsplit('.', 1)
            if name == servicename:
                return True
        return False

    def restartService(self, servicename):
        return j.system.process.execute("sudo systemctl restart %s" % servicename, False)

    def statusService(self, servicename):
        exitcode, _ = j.system.process.execute("sudo systemctl is-active %s" % servicename, False)
        return exitcode == 0

    def serviceDisableStartAtBoot(self, servicename):
        if '%s.service' % servicename in self.listServices():
            j.system.process.execute("sudo systemctl disable %s" % servicename)

    def serviceEnableStartAtBoot(self, servicename):
        j.system.process.execute("sudo systemctl enable %s" % servicename)

    def installDebFile(self, path, installDeps=True):
        self.check()
        j.system.process.execute('dpkg -i %s' % path)
        if installDeps:
            j.system.process.execute('apt-get -y install -f')

    def updatePackageMetadata(self, force=True):
        j.system.process.execute('apt-get update')
