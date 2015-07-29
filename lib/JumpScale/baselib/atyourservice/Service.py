from JumpScale import j
import JumpScale.baselib.actions
import JumpScale.baselib.packInCode
import JumpScale.baselib.remote.cuisine
from collections import OrderedDict

import imp
import sys
from functools import wraps


def log(msg, level=1):
    j.logger.log(msg, level=level, category='JSERVICE')


def loadmodule(name, path):
    parentname = ".".join(name.split(".")[:-1])
    sys.modules[parentname] = __package__
    mod = imp.load_source(name, path)
    return mod

# decorator to get dependencies


def deps(F):  # F is func or method without instance
    def processresult(result, newresult):
        """
        this makes sure we can concatenate the results in an intelligent way for all deps
        """
        if isinstance(newresult, str):
            if result is None:
                result = ""
            result += newresult
        elif newresult is None:
            pass
        elif isinstance(newresult, dict):
            if result is None:
                result = {}
            result.update(newresult)
        elif isinstance(newresult, list):
            if result is None:
                result = []
            for item in newresult:
                if item not in result:
                    result.append(item)
        elif isinstance(newresult, bool):
            if result is None:
                result = True
            result = result and newresult
        elif isinstance(newresult, int):
            if result is None:
                result = 0
            result += newresult
        else:
            raise RuntimeError(
                "did not expect this result, needs to be str,list,bool,int,dict")
        return result

    @wraps(F)
    # class instance in args[0] for method
    def wrapper(service, *args, **kwargs):
        result = None
        deps = kwargs.pop('deps', False)
        reverse = kwargs.get('reverse', False)
        processed = kwargs.get('processed', {})
        if deps:
            packagechain = service.getDependencyChain()
            packagechain.append(service)
            processed[F.func_name] = packagechain
            if reverse:
                packagechain.reverse()
            for dep in packagechain:
                if dep in processed.get(F.func_name):
                    dep.args = service.args
                    result = processresult(result, F(dep, *args, deps=False, **kwargs))
        else:
            result = processresult(
                result, F(service, *args, deps=False, **kwargs))
        return result
    return wrapper

class Service(object):

    def __init__(self, domain='', name='', instance="", hrd=None, servicetemplate=None, path="", args=None, parent=None):
        self.processed = dict()
        self.domain = domain
        self.instance = instance
        self.name = name
        self.servicetemplate = servicetemplate
        self.templatepath = ""
        self.path = path or ''
        self._hrd = hrd
        self._actions = None
        self.parent = None
        self._reposDone = {}
        self.args = args or {}
        self.hrddata = {}
        self._categories = []
        self._producers = None
        self.cmd = None
        self.noremote = False
        if servicetemplate is not None:
            self.domain = servicetemplate.domain
            self.name = servicetemplate.name
            self.servicetemplate = servicetemplate
            self.templatepath = servicetemplate.metapath

        if self.path == "":
            if parent is None:
                self.path = j.system.fs.joinPaths(
                    j.dirs.getHrdDir(), "%s__%s__%s" % (self.domain, self.name, self.instance))
            else:
                self.path = j.system.fs.joinPaths(
                    parent.path, "%s__%s__%s" % (self.domain, self.name, self.instance))

        self.hrddata["service.name"] = self.name
        self.hrddata["service.domain"] = self.domain
        self.hrddata["service.instance"] = self.instance
        self._init = False
        self.parent = parent
        # if self.parent is not None:
        #     chain = self._parentChain(self.parent)
        #     if len(chain) > 0:
        #         self.hrddata["service.parents"]= chain


    def _parentChain(self, parent):
        chain = []
        while parent is not None:
            chain.append(parent.name)
            parent = parent.parent
        return chain

    @property
    def hrd(self):
        hrdpath = j.system.fs.joinPaths(self.path, "service.hrd")
        if self._hrd:
            return self._hrd
        if not j.system.fs.exists(hrdpath):
            self._apply()
        else:
            self._hrd = j.core.hrd.get(hrdpath, prefixWithName=False)
        return self._hrd

    @property
    def actions(self):
        if self._actions is None:
            self._loadActions()
        return self._actions

    @property
    def producers(self):
        # Get each time in case updated
        self._producers = self.hrd.getDictFromPrefix("producer")
        return self._producers

    @property
    def categories(self):
        return self.hrd.getList("service.category", [])

    @property
    def id(self):
        return j.atyourservice.getId(self.domain, self.name, self.instance, self.parent)

    def init(self):
        if self._init is False:
            if self.parent is None:
                parents = j.atyourservice.findParents(self, limit=1)
                if len(parents) >= 1:
                    self.parent = parents[0]

            self.log("init")

        self._init = True

    def getLogPath(self):
        logpath = j.system.fs.joinPaths(j.dirs.logDir, "startup", "%s_%s_%s.log" % (
            self.domain, self.name, self.instance))
        return logpath

    def isInstalled(self):
        checksumpath = j.system.fs.joinPaths(self.path, "installed.version")
        if j.system.fs.exists(checksumpath) and self.hrd.exists('service.installed.checksum'):
            return True
        return False

    def isLatest(self):
        if not self.isInstalled():
            return False
        checksum = self.hrd.get('service.installed.checksum')
        checksumpath = j.system.fs.joinPaths(self.path, "installed.version")
        installedchecksum = j.system.fs.fileGetContents(checksumpath).strip()
        if checksum != installedchecksum:
            return False
        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            branch = recipeitem.get('branch', 'master') or 'master'
            recipeurl = recipeitem['url']
            if recipeurl in self._reposDone:
                continue

            login = j.application.config.get("whoami.git.login").strip()
            passwd = j.application.config.getStr("whoami.git.passwd").strip()
            _, _, _, _, dest, url = j.do.getGitRepoArgs(
                recipeurl, login=login, passwd=passwd)

            current = j.system.process.execute(
                'cd %s; git rev-parse HEAD --branch %s' % (dest, branch))
            current = current[1].split('--branch')[1].strip()
            remote = j.system.process.execute(
                'git ls-remote %s refs/heads/%s' % (url, branch))
            remote = remote[1].split()[0]

            if current != remote:
                return False
            self._reposDone[recipeurl] = dest
        return True

    def _getMetaChecksum(self):
        return j.system.fs.getFolderMD5sum(self.templatepath)

    def getTCPPorts(self, processes=None, *args, **kwargs):
        ports = set()
        if processes is None:
            processes = self.getProcessDicts()
        for process in self.getProcessDicts():
            for item in process.get("ports", []):
                if isinstance(item, basestring):
                    moreports = item.split(";")
                elif isinstance(item, int):
                    moreports = [item]
                for port in moreports:
                    if isinstance(port, int) or port.isdigit():
                        ports.add(int(port))
        return list(ports)

    def getPriority(self):
        processes = self.getProcessDicts()
        if processes:
            return processes[0].get('prio', 100)
        return 199

    def _loadActions(self):
        if self.templatepath != "":
            self._apply()
        else:
            self._loadActionModule()

    def _loadActionModule(self):
        modulename = "JumpScale.atyourservice.%s.%s.%s" % (
            self.domain, self.name, self.instance)
        mod = loadmodule(modulename, "%s/actions.py" % self.path)
        self._actions = mod.Actions()

    def _apply(self):
        j.do.createDir(self.path)
        source = "%s/actions.py" % self.templatepath
        j.do.copyFile(source, "%s/actions.py" % self.path)
        source = "%s/actions.lua" % self.templatepath
        if j.system.fs.exists(source):
            j.do.copyFile(source, "%s/actions.lua" % self.path)

        hrdpath = j.system.fs.joinPaths(self.path, "service.hrd")
        mergeArgsHDRData = self.args.copy()
        mergeArgsHDRData.update(self.hrddata)
        mergeArgsHDRData['service.installed.checksum'] = self._getMetaChecksum()
        self._hrd = j.core.hrd.get(
            hrdpath, args=mergeArgsHDRData, prefixWithName=False)
        self._hrd.applyTemplates(
            path="%s/service.hrd" % self.templatepath, prefix="service")
        self._hrd.applyTemplates(
            path="%s/instance.hrd" % self.templatepath, prefix="instance")

        actionPy = "%s/actions.py" % self.path
        self._hrd.applyOnFile(actionPy, additionalArgs=self.args)
        j.application.config.applyOnFile(actionPy, additionalArgs=self.args)

        actionLua = "%s/actions.lua" % self.path
        if j.system.fs.exists(source):
            self._hrd.applyOnFile(actionLua, additionalArgs=self.args)
            j.application.config.applyOnFile(
                actionLua, additionalArgs=self.args)

        j.application.config.applyOnFile(hrdpath, additionalArgs=self.args)
        self._hrd.process("")  # replace $() with actual data

        self._loadActionModule()

    def _getRepo(self, url, recipeitem=None, dest=None):
        if url in self._reposDone:
            return self._reposDone[url]

        login = None
        passwd = None
        if recipeitem is not None and "login" in recipeitem:
            login = recipeitem["login"]
            if login == "anonymous" or login.lower() == "none" or login == "" or login.lower() == "guest":
                login = "guest"
        if recipeitem is not None and "passwd" in recipeitem:
            passwd = recipeitem["passwd"]

        branch = 'master'
        if recipeitem is not None and "branch" in recipeitem:
            branch = recipeitem["branch"]

        revision = None
        if recipeitem is not None and "revision" in recipeitem:
            revision = recipeitem["revision"]

        depth = 1
        if recipeitem is not None and "depth" in recipeitem:
            depth = recipeitem["depth"]
            if isinstance(depth, str) and depth.lower() == "all":
                depth = None
            else:
                depth = int(depth)

        login = j.application.config.get("whoami.git.login").strip()
        passwd = j.application.config.getStr("whoami.git.passwd").strip()

        dest = j.do.pullGitRepo(url=url, login=login, passwd=passwd,
                                depth=depth, branch=branch, revision=revision, dest=dest)
        self._reposDone[url] = dest
        return dest

    def getDependencies(self, build=False):
        """
        @param build: Include build dependencies
        @type build: bool
        """
        res = []

        def sorter(item):
            parts = item[0].split('.')
            if parts[-1].isdigit():
                return int(parts[-1])
            return item

        deps = OrderedDict(sorted(self.hrd.getDictFromPrefix("service.dependencies").iteritems(), key=sorter))

        for item in deps.values():
            if isinstance(item, str):
                if item.strip() == "":
                    continue
                hrddata = {}
                item = {}
                item["name"] = item.strip()
                item["domain"] = ""
                item["instance"] = "main"

            if not build and item.get('type', 'runtime') == 'build':
                continue

            if "args" in item:
                if isinstance(item['args'], dict):
                    hrddata = {}
                    for k, v in item['args'].iteritems():
                        hrddata["instance.%s" % k] = v
                    hrddata = item['args']
                else:
                    argskey = item['args']
                    if self.hrd.exists('service.'+argskey):
                        argsDict = self.hrd.getDict('service.'+argskey)
                        hrddata = {}
                        for k, v in argsDict.iteritems():
                            hrddata["instance.%s" % k] = v
                    else:
                        hrddata = {}
            else:
                hrddata = {}

            if "name" in item:
                name = item["name"]

            domain = ""
            if "domain" in item:
                domain = item["domain"].strip()
            # if domain=="":
            #     domain="jumpscale"

            instance = "main"
            if "instance" in item:
                instance = item["instance"].strip()
            if instance == "":
                instance = "main"
            services = j.atyourservice.findServices(name=name, instance=instance, parent=self.parent, precise=True)
            if len(services) > 0:
                service = services[0]
            else:
                print "Dependecy %s_%s_%s not found, creating ..." % (domain, name, instance)
                service = j.atyourservice.new(domain=domain, name=name, instance=instance, path='', args=hrddata, parent=self.parent)
                if self.noremote is False and len(self.producers):
                    for cat, prod in self.producers.iteritems():
                        service.init()
                        service.consume(cat, prod)
                service.noremote = self.noremote

            res.append(service)

        return res

    def log(self, msg):
        logpath = j.system.fs.joinPaths(self.path, "log.txt")
        if not j.system.fs.exists(self.path):
            j.system.fs.createDir(self.path)
        msg = "%s : %s\n" % (
            j.base.time.formatTime(j.base.time.getTimeEpoch()), msg)
        j.system.fs.writeFile(logpath, msg, append=True)

    def listChildren(self):
        childDirs = j.system.fs.listDirsInDir(self.path)
        childs = {}
        for path in childDirs:
            child = j.system.fs.getBaseName(path)
            ss = child.split("__")
            name = ss[0]
            instance = ss[1]
            if name not in childs:
                childs[name] = []
            childs[name].append(instance)
        return childs

    def getDependencyChain(self, chain=None):
        chain = chain if chain is not None else []
        dependencies = self.getDependencies()
        for dep in dependencies:
            dep.getDependencyChain(chain)
            if self in chain:
                if dep not in chain:
                    chain.insert(chain.index(self)+1, dep)
                if dep in chain and chain.index(dep) > chain.index(self):
                    dependant = chain.pop(self)
                    chain.insert(chain.index(dep), dependant)
            else:
                if dep not in chain:
                    chain.append(dep)
        return chain

    def __eq__(self, service):
        if service is None:
            return False
        return service.name == self.name and self.domain == service.domain and self.instance == service.instance

    def stop(self, deps=True):
        self.log("stop instance")
        self.actions.stop(self)
        if not self.actions.check_down_local(self):
            self.actions.halt(self)

    # @deps
    def build(self, deps=True, processed={}):
        self.log("build instance")
        for dep in self.getDependencies(build=True):
            if dep.name not in j.atyourservice._justinstalled:
                dep.install()
                j.atyourservice._justinstalled.append(dep.name)

        for recipeitem in self.hrd.getListFromPrefix("service.git.export"):
            # pull the required repo
            self._getRepo(recipeitem['url'], recipeitem=recipeitem)

        for recipeitem in self.hrd.getListFromPrefix("service.git.build"):
            # pull the required repo
            name = recipeitem['url'].replace(
                "https://", "").replace("http://", "").replace(".git", "")
            self._getRepo(
                recipeitem['url'], recipeitem=recipeitem, dest="/opt/build/%s" % name)
            self.actions.build(self)

    @deps
    def start(self, deps=True, processed={}):
        self.log("start instance")
        self.actions.start(self)

    @deps
    def restart(self, deps=True, processed={}):
        self.stop()
        self.start()

    def getProcessDicts(self, deps=True, args={}):
        counter = 0

        defaults = {"prio": 10, "timeout_start": 10,
                    "timeout_start": 10, "startupmanager": "tmux"}
        musthave = ["cmd", "args", "prio", "env", "cwd", "timeout_start",
                    "timeout_start", "ports", "startupmanager", "filterstr", "name", "user"]

        procs = self.hrd.getListFromPrefixEachItemDict("service.process", musthave=musthave, defaults=defaults, aredict=[
                                                       'env'], arelist=["ports"], areint=["prio", "timeout_start", "timeout_start"])
        for process in procs:
            counter += 1

            process["test"] = 1

            if process["name"].strip() == "":
                process["name"] = "%s_%s" % (
                    self.hrd.get("service.name"), self.hrd.get("service.instance"))

            if self.hrd.exists("env.process.%s" % counter):
                process["env"] = self.hrd.getDict("env.process.%s" % counter)

            if not isinstance(process["env"], dict):
                raise RuntimeError("process env needs to be dict")

        return procs

    @deps
    def prepare(self, deps=True, reverse=True, processed={}):
        self.log("prepare install for instance")
        if j.do.TYPE.startswith("UBUNTU"):

            for src in self.hrd.getListFromPrefix("service.ubuntu.apt.source"):
                src = src.replace(";", ":")
                if src.strip() != "":
                    j.system.platform.ubuntu.addSourceUri(src)

            for src in self.hrd.getListFromPrefix("service.ubuntu.apt.key.pub"):
                src = src.replace(";", ":")
                if src.strip() != "":
                    cmd = "wget -O - %s | apt-key add -" % src
                    j.do.execute(cmd, dieOnNonZeroExitCode=False)

            if self.hrd.getBool("service.ubuntu.apt.update", default=False):
                log("apt update")
                j.do.execute("apt-get update -y", dieOnNonZeroExitCode=False)

            if self.hrd.getBool("service.ubuntu.apt.upgrade", default=False):
                j.do.execute("apt-get upgrade -y", dieOnNonZeroExitCode=False)

            if self.hrd.exists("service.ubuntu.packages"):
                packages = self.hrd.getList("service.ubuntu.packages")
                packages = [pkg.strip() for pkg in packages if pkg.strip() != ""]
                if packages:
                    j.do.execute("apt-get install -y -f %s" %
                                 " ".join(packages), dieOnNonZeroExitCode=True)

        self.actions.prepare(self)

    @deps
    def install(self, start=True, deps=True, reinstall=False, processed={}):
        """
        Install Service.

        Keyword arguments:
        start     -- whether Service should start after install (default True)
        deps      -- install the Service dependencies (default True)
        reinstall -- reinstall if already installed (default False)
        """
        def hrdChanged():
            for key, value in self.args.items():
                if not self.hrd.get(key, '') == value:
                    self.hrd.set(key, value)
            return self.hrd.changed

        self.init()
        if reinstall:
            self.resetstate()

        log("INSTALL:%s" % self)
        if self.isLatest() and not reinstall and not hrdChanged():
            log("Latest %s already installed" % self)
            return
        self.stop(deps=False)
        self.prepare(deps=deps, reverse=True)
        self.log("install instance")
        self._install(start=start, deps=deps, reinstall=reinstall)

    def _install(self, start=True, deps=True, reinstall=False):
        # download
        for recipeitem in self.hrd.getListFromPrefix("service.web.export"):
            if "dest" not in recipeitem:
                raise RuntimeError(
                    "could not find dest in hrditem for %s %s" % (recipeitem, self))
            fullurl = "%s/%s" % (recipeitem['url'],
                                 recipeitem['source'].lstrip('/'))
            dest = recipeitem['dest']
            destdir = j.system.fs.getDirName(dest)
            j.system.fs.createDir(destdir)
            # validate md5sum
            if recipeitem.get('checkmd5', 'false').lower() == 'true' and j.system.fs.exists(dest):
                remotemd5 = j.system.net.download(
                    '%s.md5sum' % fullurl, '-').split()[0]
                localmd5 = j.tools.hash.md5(dest)
                if remotemd5 != localmd5:
                    j.system.fs.remove(dest)
                else:
                    continue
            elif j.system.fs.exists(dest):
                j.system.fs.remove(dest)
            j.system.net.download(fullurl, dest)

        for recipeitem in self.hrd.getListFromPrefix("service.git.export"):
            if recipeitem.has_key("platform"):
                if not j.system.platformtype.checkMatch(recipeitem["platform"]):
                    continue

            # print recipeitem
            # pull the required repo
            dest0 = self._getRepo(recipeitem['url'], recipeitem=recipeitem)
            src = "%s/%s" % (dest0, recipeitem['source'])
            src = src.replace("//", "/")
            if "dest" not in recipeitem:
                raise RuntimeError(
                    "could not find dest in hrditem for %s %s" % (recipeitem, self))
            dest = recipeitem['dest']

            if "link" in recipeitem and str(recipeitem["link"]).lower() == 'true':
                # means we need to only list files & one by one link them
                link = True
            else:
                link = False

            if src[-1] == "*":
                src = src.replace("*", "")
                if "nodirs" in recipeitem and str(recipeitem["nodirs"]).lower() == 'true':
                    # means we need to only list files & one by one link them
                    nodirs = True
                else:
                    nodirs = False

                items = j.do.listFilesInDir(
                    path=src, recursive=False, followSymlinks=False, listSymlinks=False)
                if nodirs is False:
                    items += j.do.listDirsInDir(
                        path=src, recursive=False, dirNameOnly=False, findDirectorySymlinks=False)

                items = [(item, "%s/%s" % (dest, j.do.getBaseName(item)), link)
                         for item in items]
            else:
                items = [(src, dest, link)]

            for src, dest, link in items:
                delete = recipeitem.get('overwrite', 'true').lower() == "true"
                if dest.strip() == "":
                    raise RuntimeError(
                        "a dest in coderecipe cannot be empty for %s" % self)
                if dest[0] != "/":
                    dest = "/%s" % dest
                else:
                    if link:
                        if not j.system.fs.exists(dest):
                            j.system.fs.createDir(j.do.getParent(dest))
                            j.do.symlink(src, dest)
                        elif delete:
                            j.system.fs.remove(dest)
                            j.do.symlink(src, dest)
                    else:
                        print("copy: %s->%s" % (src, dest))
                        if j.system.fs.isDir(src):
                            j.system.fs.createDir(j.system.fs.getParent(dest))
                            j.system.fs.copyDirTree(
                                src, dest, eraseDestination=False, overwriteFiles=delete)
                        else:
                            j.system.fs.copyFile(
                                src, dest, True, overwriteFile=delete)

        self.configure(deps=False)

        self.start()
        j.system.fs.writeFile(j.system.fs.joinPaths(self.path, "installed.version"), self.hrd.get('service.installed.checksum'))

        # else:
        #     #now bootstrap docker
        #     ports=""
        #     tcpports=self.hrd.getDict("docker.ports.tcp")
        #     for inn,outt in tcpports.items():
        #         ports+="%s:%s "%(inn,outt)
        #     ports=ports.strip()

        #     volsdict=self.hrd.getDict("docker.vols")
        #     vols=""
        #     for inn,outt in volsdict.items():
        #         vols+="%s:%s # "%(inn,outt)
        #     vols=vols.strip().strip("#").strip()

        #     if self.instance!="main":
        #         name="%s_%s"%(self.service.name,self.instance)
        #     else:
        #         name="%s"%(self.service.name)

        #     image=self.hrd.get("docker.base",default="despiegk/mc")

        #     mem=self.hrd.get("docker.mem",default="0")
        #     if mem.strip()=="":
        #         mem=0

        #     cpu=self.hrd.get("docker.cpu",default=None)
        #     if cpu.strip()=="":
        #         cpu=None

        #     ssh=self.hrd.get("docker.ssh",default=True)
        #     if ssh.strip()=="":
        #         ssh=True

        #     ns=self.hrd.get("docker.ns",default='8.8.8.8')
        #     if ns.strip()=="":
        #         ns='8.8.8.8'

        #     port=   j.tools.docker.create(name=name, ports=ports, vols=vols, volsro='', stdout=True, base=image, nameserver=ns, \
        #         replace=True, cpu=cpu, mem=0,jumpscale=True,ssh=ssh)

        #     self.hrd.set("docker.ssh.port",port)
        #     self.hrd.set("docker.name",name)
        #     self.hrd.save()

        #     hrdname="service.%s.%s.%s.hrd"%(self.service.domain,self.service.name,self.instance)
        #     src="/%s/hrd/apps/%s"%(j.dirs.baseDir,hrdname)
        #     j.tools.docker.copy(name,src,src)
        #     j.tools.docker.run(name,"service install -n %s -d %s"%(self.service.name,self.service.domain))

    @deps
    def publish(self, deps=True, processed={}):
        """
        check which repo's are used & push the info
        this does not use the build repo's
        """
        self.log("publish instance")
        self.actions.publish(self)

    @deps
    def package(self, deps=True, processed={}):
        """
        """
        self.actions.package(self)

    @deps
    def update(self, deps=True, processed={}):
        """
        - go over all related repo's & do an update
        - copy the files again
        - restart the app
        """
        self.log("update instance")
        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            # pull the required repo
            self._getRepo(recipeitem['url'], recipeitem=recipeitem)

        for recipeitem in self.hrd.getListFromPrefix("git.build"):
            # print recipeitem
            # pull the required repo
            name = recipeitem['url'].replace(
                "https://", "").replace("http://", "").replace(".git", "")
            dest = "/opt/build/%s/%s" % name
            j.do.pullGitRepo(dest=dest, ignorelocalchanges=True)

        self.restart()

    @deps
    def resetstate(self, deps=True, processed={}):
        """
        remove state of a service.
        """
        statePath = j.system.fs.joinPaths(self.path, 'state.json')
        j.do.delete(statePath)

    @deps
    def reset(self, deps=True, processed={}):
        """
        - remove build repo's !!!
        - remove state of the app (same as resetstate) in jumpscale (the configuration info)
        - remove data of the app
        """
        self.log("reset instance")
        # remove build repo's
        for recipeitem in self.hrd.getListFromPrefix("git.build"):
            name = recipeitem['url'].replace(
                "https://", "").replace("http://", "").replace(".git", "")
            dest = "/opt/build/%s" % name
            j.do.delete(dest)

        self.actions.removedata(self)
        j.atyourservice.remove(self)

    @deps
    def removedata(self, deps=False, processed={}):
        """
        - remove build repo's !!!
        - remove state of the app (same as resetstate) in jumpscale (the configuration info)
        - remove data of the app
        """
        self.log("removedata instance")
        self.actions.removedata(self)

    @deps
    def execute(self, cmd=None, deps=False, processed={}):
        """
        execute cmd on service
        """
        if cmd is None:
            cmd = self.cmd
        self.actions.execute(self, cmd=cmd)

    @deps
    def uninstall(self, deps=True, processed={}):
        self.log("uninstall instance")
        self.reset()
        self.actions.uninstall(self)

    @deps
    def monitor(self, deps=True, processed={}):
        """
        do all monitor checks and return True if they all succeed
        """
        res = self.actions.check_up_local(self)
        res = res and self.actions.monitor_local(self)
        res = res and self.actions.monitor_remove(self)
        return res

    @deps
    def iimport(self, url, deps=True, processed={}):
        self.log("import instance data")
        self.actions.data_import(url, self)

    @deps
    def export(self, url, deps=True, processed={}):
        self.log("export instance data")
        self.actions.data_export(url, self)

    @deps
    def configure(self, deps=True, restart=True, processed={}):
        self.log("configure instance")
        self.actions.configure(self)
        # if restart:
        # self.restart(deps=False)

    def findParents(self):
        return j.atyourservice.findParents(self)

    def consume(self, producercategory, instancename):
        """
        create connection between consumer (this service) & producer
        producer category is category of service
        """
        candidates = j.atyourservice.findServices(instance=instancename)
        items = [x for x in candidates if producercategory in x.categories]
        for item in items:
            self.hrd.set("producer.%s" % producercategory, item.instance)

        if not items:
            raise RuntimeError(
                "Could not find producer:%s for instance:%s" % (producercategory, instancename))

    def getProducer(self, producercategory):
        if producercategory not in self.producers:
            # j.events.inputerror_warning("cannot find producer with category:%s"%producercategory,"ays.getProducer")
            return None
        instancename = self.producers[producercategory]
        return j.atyourservice.findProducer(producercategory, instancename)

    def __repr__(self):
        return "%-15s:%-15s:%s" % (self.domain, self.name, self.instance)

    def __str__(self):
        return self.__repr__()
