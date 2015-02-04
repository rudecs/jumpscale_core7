from JumpScale import j
import imp
import sys

import JumpScale.baselib.actions
import JumpScale.baselib.packInCode
import JumpScale.baselib.remote.cuisine

def log(msg, level=1):
    j.logger.log(msg, level=level, category='JPACKAGE')

def loadmodule(name, path):
    parentname = ".".join(name.split(".")[:-1])
    sys.modules[parentname] = __package__
    mod = imp.load_source(name, path)
    return mod

#decorator to execute an action on a remote machine
def remote(F): # F is func or method without instance
    def wrapper(jp, *args,**kwargs): # class instance in args[0] for method
        jp.init()
        if not jp.node:
            return F(jp, *args,**kwargs)
        else:
            node = jp.node
            if jp.args.get('lua', False):
                cl = j.packages.remote.sshLua(jp, node)
            else:
                cl = j.packages.remote.sshPython(jp, node)

            cl.execute(F.func_name)
    wrapper.func_name_orig = F.func_name
    return wrapper

#decorator to get dependencies
def deps(F): # F is func or method without instance
    def processresult(result,newresult):
        """
        this makes sure we can concatenate the results in an intelligent way for all deps
        """
        if isinstance(newresult,str):
            if result==None:
                result=""
            result+=newresult
        elif newresult==None:
            pass
        elif isinstance(newresult,dict):
            if result==None:
                result={}
            result.update(newresult)
        elif isinstance(newresult,list):
            if result==None:
                result=[]
            for item in newresult:
                if item not in result:
                    result.append(item)
        elif isinstance(newresult,bool):
            if result==None:
                result=True
            result=result and newresult
        elif isinstance(newresult,int):
            if result==None:
                result=0
            result+=newresult
        else:
            raise RuntimeError("did not expect this result, needs to be str,list,bool,int,dict")
        return result

    def wrapper(jp, *args,**kwargs): # class instance in args[0] for method
        result=None

        deps = kwargs.get('deps', False)
        if deps:
            j.packages._justinstalled=[]
            for dep in jp.getDependencies():
                if dep.jp.name not in j.packages._justinstalled:
                    dep.args = jp.args
                    if hasattr(F, 'func_name_orig'):
                        depfunc = getattr(dep, F.func_name_orig)
                    else:
                        depfunc = getattr(dep, F.func_name)
                    result=processresult(result,depfunc(*args, **kwargs))
                    j.packages._justinstalled.append(dep.jp.name)
        result=processresult(result,F(jp, *args,**kwargs))
        return result
    return wrapper

class JPackage():

    def __init__(self,domain="",name=""):
        self.name=name
        self.domain=domain
        self.hrd=None
        self.metapath="%s/%s"%(j.packages.domains[self.domain],self.name)
        self.hrdpath=""
        self.hrdpath_main=""

    def getInstance(self,instance=None, args={}, hrddata=None,node=""):
        # get first installed or main
        if instance is None:
            instances = self.listInstances(node=node)
            if instances:
                instance = instances[0]
            else:
                instance = 'main'
        return JPackageInstance(self, instance, args, hrddata,node=node)

    def existsInstance(self,instance,node=""):
        # get first installed or main
        instances = self.listInstances(node=node)
        if instances:
            return True
        else:
            return False

    def listInstances(self, node=None):
        hrdfolder = j.dirs.getHrdDir(node=node)
        files = j.system.fs.find(hrdfolder, self.getHRDPattern(node))
        instances = list()
        for path in files:
            instances.append(path.split('.')[-2])
        return instances

    def getHRDPattern(self,node=None):
        if j.packages.type=="c":
            hrdpath = "%s.*.hrd" % (self.name)
        else:
            hrdpath = "%s.%s.*.hrd" % (self.domain, self.name)
        return hrdpath

    def __repr__(self):
        return "%-15s:%s"%(self.domain,self.name)

    def __str__(self):
        return self.__repr__()

class JPackageInstance(object):

    def __init__(self,jp,instance, args=None, hrddata=None,node=""):
        self.instance=instance
        self.jp=jp
        self.domain=self.jp.domain
        self.name=self.jp.name
        self._hrd=None
        self._actionspath = None
        self.metapath = jp.metapath
        self._hrdpath = None
        self._actions=None
        self._loaded=False
        self._reposDone={}
        self.args=args or {}
        self.hrddata = hrddata or {}
        self.hrddata["jp.name"]=self.jp.name
        self.hrddata["jp.domain"]=self.jp.domain
        self.hrddata["jp.instance"]=self.instance
        self._init=False
        self.node = self.args.get("node2execute","")
        if self.node=="" and node!="":
            self.node=node


    @property
    def hrdpath(self):
        self._hrdpath = self.getHRDPath()
        return self._hrdpath

    @property
    def hrd(self):
        if not j.system.fs.exists(self.hrdpath):
            self._apply()
        self._hrd = j.core.hrd.get(self.hrdpath)
        return self._hrd

    @property
    def actions(self):
        if self._actions is None:
            self._loadActions()
        return self._actions

    @property
    def actionspath(self):
        if self._actionspath is None:
            actionsdir = j.dirs.getJPActionsPath(node=self.node)
            j.system.fs.createDir(actionsdir)
            if j.packages.type=="c":
                j.system.fs.createDir(j.dirs.getJPActionsPath(node=self.node))
                self._actionspath="%s/%s__%s"%(actionsdir,self.jp.name,self.instance)
            else:
                self._actionspath="%s/%s__%s__%s"%(actionsdir,self.jp.domain,self.jp.name,self.instance)
        return self._actionspath

    def init(self):
        if self._init==False:
            import JumpScale.baselib.remote.cuisine
            import JumpScale.lib.docker
            if self.actions.init():
                #did something
                pass
                #@todo need to reload HRD's
        self._init=True

    def getLogPath(self):
        logpath=j.system.fs.joinPaths(j.dirs.logDir,"startup", "%s_%s_%s.log" % (self.jp.domain, self.jp.name,self.instance))
        return logpath

    def getHRDPath(self):
        if j.packages.type=="c":
            hrdpath = "%s/%s.%s.hrd" % (j.dirs.getHrdDir(node=self.node), self.jp.name, self.instance)
        else:
            hrdpath = "%s/%s.%s.%s.hrd" % (j.dirs.getHrdDir(), self.jp.domain, self.jp.name, self.instance)
        return hrdpath

    def isInstalled(self):
        hrdpath = self.getHRDPath()
        if j.system.fs.exists(hrdpath) and self.hrd.exists('jp.installed.checksum'):
            return True
        return False

    def isLatest(self):
        if not self.isInstalled():
            return False
        checksum = self.hrd.get('jp.installed.checksum')
        return checksum == self._getMetaChecksum()

    def _getMetaChecksum(self):
        return j.system.fs.getFolderMD5sum(self.metapath)

    def getTCPPorts(self,deps=True, *args, **kwargs):
        ports = set()
        for process in self.getProcessDicts():
            for item in process["ports"]:
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
        if not j.system.fs.exists(self.actionspath):
            self._apply()
        else:
            self._loadActionModule()

    def _loadActionModule(self):
        modulename="JumpScale.jpackages.%s.%s.%s"%(self.jp.domain,self.jp.name,self.instance)
        mod = loadmodule(modulename, self.actionspath+".py")

        self._actions=mod.Actions()
        self._actions.jp_instance=self

    def _apply(self):
        j.do.createDir(j.do.getDirName(self.hrdpath))
        source="%s/actions.py"%self.jp.metapath
        j.do.copyFile(source,self.actionspath+".py")
        source="%s/actions.lua"%self.jp.metapath
        if j.system.fs.exists(source):
            j.do.copyFile(source,self.actionspath+".lua")

        self._hrd=j.core.hrd.get(self.hrdpath,args=self.hrddata,templates=["%s/instance.hrd"%self.jp.metapath,"%s/jp.hrd"%self.jp.metapath])
        self._hrd.save()
       
        actionPy = self.actionspath+".py"
        self._hrd.applyOnFile(actionPy, additionalArgs=self.args)
        j.application.config.applyOnFile(actionPy, additionalArgs=self.args)

        actionLua = self.actionspath+".lua"
        if j.system.fs.exists(source):
            self._hrd.applyOnFile(actionLua, additionalArgs=self.args)
            j.application.config.applyOnFile(actionLua, additionalArgs=self.args)

        j.application.config.applyOnFile(self.hrdpath, additionalArgs=self.args)

        self._loadActionModule()


    def _getRepo(self,url,recipeitem=None,dest=None):
        if url in self._reposDone:
            return self._reposDone[url]

        login=None
        passwd=None
        if recipeitem<>None and "login" in recipeitem:
            login=recipeitem["login"]
            if login=="anonymous" or login.lower()=="none" or login=="" or login.lower()=="guest" :
                login="guest"
        if recipeitem<>None and "passwd" in recipeitem:
            passwd=recipeitem["passwd"]

        branch='master'
        if recipeitem<>None and "branch" in recipeitem:
            branch=recipeitem["branch"]

        revision=None
        if recipeitem<>None and "revision" in recipeitem:
            revision=recipeitem["revision"]

        depth=1
        if recipeitem<>None and "depth" in recipeitem:
            depth=recipeitem["depth"]
            if isinstance(depth,str) and depth.lower()=="all":
                depth=None
            else:
                depth=int(depth)

        login = j.application.config.get("whoami.git.login").strip()
        passwd = j.application.config.getStr("whoami.git.passwd").strip()

        dest=j.do.pullGitRepo(url=url, login=login, passwd=passwd, depth=depth, branch=branch,revision=revision,dest=dest)
        self._reposDone[url]=dest
        return dest

    def getDependencies(self, build=False):
        """
        @param build: Include build dependencies
        @type build: bool
        """
        res=[]
        for item in self.hrd.getListFromPrefix("dependencies"):

            if isinstance(item,str):
                if item.strip()=="":
                    continue
                item2=item.strip()
                hrddata={}
                item={}
                item["name"]=item2
                item["domain"]=""
                item["instance"]="main"

            if not build and item.get('type', 'runtime') == 'build':
                continue

            if "args" in item:
                if isinstance(item['args'], dict):
                    hrddata = item['args']
                else:
                    argskey = item['args']
                    if self.hrd.exists(argskey):
                        hrddata=self.hrd.getDict(argskey)
                    else:
                        hrddata = {}
            else:
                hrddata={}

            if "name" in item:
                name=item["name"]

            domain=""
            if "domain" in item:
                domain=item["domain"].strip()
            # if domain=="":
            #     domain="jumpscale"

            instance="main"
            if "instance" in item:
                instance=item["instance"].strip()
            if instance=="":
                instance="main"

            jp=j.packages.get(name=name,domain=domain)
            jp=jp.getInstance(instance, hrddata=hrddata)

            res.append(jp)

        return res

    @deps
    @remote
    def stop(self,deps=True):
        self.actions.stop(**self.args)
        if not self.actions.check_down_local(**self.args):
            self.actions.halt(**self.args)

    # @deps
    def build(self, deps=True):

        if self.node:
            node = j.packages.remote.sshPython(jp=self.jp,node=self.node)
        else:
            node = None

        for dep in self.getDependencies(build=True):
            if dep.jp.name not in j.packages._justinstalled:
                if 'args' in dep.__dict__:
                    dep.install(args=dep.args)
                else:
                    dep.install()
                j.packages._justinstalled.append(dep.jp.name)

        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            #pull the required repo
            self._getRepo(recipeitem['url'],recipeitem=recipeitem)

        for recipeitem in self.hrd.getListFromPrefix("git.build"):
            #pull the required repo
            name=recipeitem['url'].replace("https://","").replace("http://","").replace(".git","")
            self._getRepo(recipeitem['url'],recipeitem=recipeitem,dest="/opt/build/%s"%name)
            if node:
                dest = "root@%s:%s" %(node.ip, "/opt/build/%s"%name)
                node.copyTree("/opt/build/%s"%name,dest)
        if node:
            self._build()
        else:
            self.actions.build(**self.args)

    @remote
    def _build(self,deps=True):
        self.action.build(**self.args)

    @deps
    @remote
    def start(self,deps=True):
        self.actions.start(**self.args)

    @deps
    def restart(self,deps=True):
        self.stop()
        self.start()

    def getProcessDicts(self,deps=True,args={}):
        counter=0

        defaults={"prio":10,"timeout_start":10,"timeout_start":10,"startupmanager":"tmux"}
        musthave=["cmd","args","prio","env","cwd","timeout_start","timeout_start","ports","startupmanager","filterstr","name","user"]

        procs=self.hrd.getListFromPrefixEachItemDict("process",musthave=musthave,defaults=defaults,aredict=['env'],arelist=["ports"],areint=["prio","timeout_start","timeout_start"])
        for process in procs:
            counter+=1

            process["test"]=1

            if process["name"].strip()=="":
                process["name"]="%s_%s"%(self.hrd.get("jp.name"),self.hrd.get("jp.instance"))

            if self.hrd.exists("env.process.%s"%counter):
                process["env"]=self.hrd.getDict("env.process.%s"%counter)

            if not isinstance(process["env"],dict):
                raise RuntimeError("process env needs to be dict")

        return procs

    @remote
    def prepare(self,deps=False):
        for src in self.hrd.getListFromPrefix("ubuntu.apt.source"):
            src=src.replace(";",":")
            if src.strip()!="":
                j.system.platform.ubuntu.addSourceUri(src)

        for src in self.hrd.getListFromPrefix("ubuntu.apt.key.pub"):
            src=src.replace(";",":")
            if src.strip()!="":
                cmd="wget -O - %s | apt-key add -"%src
                j.do.execute(cmd,dieOnNonZeroExitCode=False)

        if self.hrd.getBool("ubuntu.apt.update",default=False):
            log("apt update")
            j.do.execute("apt-get update -y",dieOnNonZeroExitCode=False)

        if self.hrd.getBool("ubuntu.apt.upgrade",default=False):
            j.do.execute("apt-get upgrade -y",dieOnNonZeroExitCode=False)

        if self.hrd.exists("ubuntu.packages"):
            packages = self.hrd.getList("ubuntu.packages")
            packages = [ pkg.strip() for pkg in packages if pkg.strip() != "" ]
            if packages:
                j.do.execute("apt-get install -y -f %s"% " ".join(packages) ,dieOnNonZeroExitCode=True)

        self.actions.prepare()

    @deps
    def install(self,start=True,deps=True, reinstall=False):
        self.init()
        if reinstall:
            self.resetstate()

        if self.node:
            node = j.packages.remote.sshPython(jp=self.jp,node=self.node)
        else:
            node = None

        log("INSTALL:%s"%self)
        if self.isLatest() and not reinstall and not node:
            log("Latest %s already installed" % self)
            return
        self._apply()
        self.stop(deps=False)
        self.prepare(deps=False)

        #download
        for recipeitem in self.hrd.getListFromPrefix("web.export"):
            if "dest" not in recipeitem:
                raise RuntimeError("could not find dest in hrditem for %s %s"%(recipeitem,self))
            fullurl = "%s/%s" % (recipeitem['url'], recipeitem['source'].lstrip('/'))
            dest = recipeitem['dest']
            destdir = j.system.fs.getDirName(dest)
            j.system.fs.createDir(destdir)
            # validate md5sum
            if recipeitem.get('checkmd5', 'false').lower() == 'true' and j.system.fs.exists(dest):
                remotemd5 = j.system.net.download('%s.md5sum' % fullurl, '-').split()[0]
                localmd5 = j.tools.hash.md5(dest)
                if remotemd5 != localmd5:
                    j.system.fs.remove(dest)
                else:
                    continue
            elif j.system.fs.exists(dest):
                j.system.fs.remove(dest)
            j.system.net.download(fullurl, dest)
            if node:
                remoteDest = "root@%s:%s" %(node.ip,dest)
                node.copyTree(dest,remoteDest)

        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            # print recipeitem
            #pull the required repo
            dest0=self._getRepo(recipeitem['url'],recipeitem=recipeitem)
            src="%s/%s"%(dest0,recipeitem['source'])
            src=src.replace("//","/")
            if "dest" not in recipeitem:
                raise RuntimeError("could not find dest in hrditem for %s %s"%(recipeitem,self))
            dest=recipeitem['dest']

            if "link" in recipeitem and str(recipeitem["link"]).lower()=='true':
                #means we need to only list files & one by one link them
                link=True
            else:
                link=False

            if src[-1]=="*":
                src=src.replace("*","")
                if "nodirs" in recipeitem and str(recipeitem["nodirs"]).lower()=='true':
                    #means we need to only list files & one by one link them
                    nodirs=True
                else:
                    nodirs=False

                items=j.do.listFilesInDir( path=src, recursive=False, followSymlinks=False, listSymlinks=False)
                if nodirs==False:
                    items+=j.do.listDirsInDir(path=src, recursive=False, dirNameOnly=False, findDirectorySymlinks=False)

                items=[(item,"%s/%s"%(dest,j.do.getBaseName(item)),link) for item in items]
            else:
                items=[(src,dest,link)]

            for src,dest,link in items:
                if dest.strip()=="":
                    raise RuntimeError("a dest in coderecipe cannot be empty for %s"%self)
                if dest[0]!="/":
                    dest="/%s"%dest
                if node:
                    # copy file on remote node with rsync
                    dest = "root@%s:%s" %(node.ip,dest)
                    node.copyTree(src,dest)
                else:
                    if link:
                        if not j.system.fs.exists(dest):
                            j.system.fs.createDir(j.do.getParent(dest))
                            j.do.symlink(src, dest)
                    else:
                        if j.system.fs.exists(path=dest):
                            if not "delete" in recipeitem:
                                recipeitem["delete"]="false"
                            if recipeitem["delete"].lower()=="true":
                                print ("copy: %s->%s"%(src,dest))
                                j.do.delete(dest)
                                j.system.fs.createDir(dest)
                            else:
                                print ("merge: %s->%s"%(src,dest))
                            j.do.copyTree(src,dest)
                        else:
                            print ("copy: %s->%s"%(src,dest))
                            j.system.fs.createDir(dest)
                            j.do.copyTree(src,dest)

        self.configure(deps=False)

        self.start()
        self.hrd.set('jp.installed.checksum', self._getMetaChecksum())

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
        #         name="%s_%s"%(self.jp.name,self.instance)
        #     else:
        #         name="%s"%(self.jp.name)

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

        #     hrdname="jpackage.%s.%s.%s.hrd"%(self.jp.domain,self.jp.name,self.instance)
        #     src="/%s/hrd/apps/%s"%(j.dirs.baseDir,hrdname)
        #     j.tools.docker.copy(name,src,src)
        #     j.tools.docker.run(name,"jpackage install -n %s -d %s"%(self.jp.name,self.jp.domain))

    @deps
    def publish(self,deps=True):
        """
        check which repo's are used & push the info
        this does not use the build repo's
        """
        self.actions.publish(**self.args)

    @deps
    def package(self,deps=True):
        """
        """
        self.actions.package(**self.args)

    @deps
    @remote
    def update(self,deps=True):
        """
        - go over all related repo's & do an update
        - copy the files again
        - restart the app
        """
        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            #pull the required repo
            self._getRepo(recipeitem['url'],recipeitem=recipeitem)

        for recipeitem in self.hrd.getListFromPrefix("git.build"):
            # print recipeitem
            #pull the required repo
            name=recipeitem['url'].replace("https://","").replace("http://","").replace(".git","")
            dest="/opt/build/%s/%s"%name
            j.do.pullGitRepo(dest=dest,ignorelocalchanges=True)

        self.restart()

    @deps
    def resetstate(self,deps=True):        
        self._load(args)

        j.do.delete(self.actionspath,force=True)
        j.do.delete(self.actionspath+"c",force=True) #for .pyc file
        actioncat="jp_%s_%s"%(self.jp.domain,self.jp.name)
        j.do.delete("%s/%s.json"%(j.dirs.getStatePath(),actioncat),force=True)


    @deps
    def reset(self,deps=True):
        """
        - remove build repo's !!!
        - remove state of the app (same as resetstate) in jumpscale (the configuration info)
        - remove data of the app
        """
        self.resetstate()
        j.do.delete(self.hrdpath,force=True)
        #remove build repo's
        for recipeitem in self.hrd.getListFromPrefix("git.build"):
            name=recipeitem['url'].replace("https://","").replace("http://","").replace(".git","")
            dest="/opt/build/%s"%name
            j.do.delete(dest)

        self.actions.removedata(**self.args)

    @deps
    @remote
    def removedata(self,deps=False):
        """
        - remove build repo's !!!
        - remove state of the app (same as resetstate) in jumpscale (the configuration info)
        - remove data of the app
        """
        self.actions.removedata(**self.args)

    @deps
    @remote
    def execute(self,deps=False):
        """
        execute cmd on jpackage
        """
        self.actions.execute(**self.args)

    @deps
    @remote
    def uninstall(self,deps=True):
        self.reset()
        self.actions.uninstall(**self.args)

    @deps
    @remote
    def monitor(self,deps=True):
        """
        do all monitor checks and return True if they all succeed
        """
        res=self.actions.check_up_local(**self.args)
        res=res and self.actions.monitor_local(**self.args)
        res=res and self.actions.monitor_remove(**self.args)
        return res

    @deps
    @remote
    def iimport(self,url,deps=True):
        self.actions.iimport(url,**self.args)

    @deps
    @remote
    def export(self,url,deps=True):
        self.actions.export(url,**self.args)


    @deps
    @remote
    def configure(self,deps=True,restart=True):
        self.actions.configure(**self.args)
        if restart:
            self.restart(deps=False)

    def __repr__(self):
        return "%-15s:%-15s:%s"%(self.jp.domain,self.jp.name,self.instance)

    def __str__(self):
        return self.__repr__()
