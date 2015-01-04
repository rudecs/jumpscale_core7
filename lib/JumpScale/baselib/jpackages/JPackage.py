from JumpScale import j
import imp
import copy

import JumpScale.baselib.actions


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

    def wrapper(*args2,**kwargs): # class instance in args[0] for method
        result=None
        jp=args2[0] #this is the self from before
        
        jp._load(**kwargs)    
        if deps:
            j.packages._justinstalled=[]
            for dep in jp.getDependencies():
                if dep.jp.name not in j.packages._justinstalled:                    
                    if 'args' in dep.__dict__:
                        result=processresult(result,F(dep,args=dep.args))
                    else:
                        result=processresult(result,F(dep))
                    j.packages._justinstalled.append(dep.jp.name)
        result=processresult(result,F(*args2,**kwargs))
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


    def getInstance(self,instance="main"):
        return JPackageInstance(self,instance)        

    def __repr__(self):
        return "%-15s:%s"%(self.domain,self.name)

    def __str__(self):
        return self.__repr__()

class JPackageInstance():

    def __init__(self,jp,instance):
        self.instance=instance
        self.jp=jp
        self.hrd=None
        self.metapath=""
        self.hrdpath=""
        self.actions=None
        self._loaded=False
        self._reposDone={}   
        self.args={} 
        self._init=False

    def _init(self):
        if self._init==False:
            import JumpScale.baselib.remote.cuisine
            import JumpScale.lib.docker    
        self._init=True

    def getLogPath(self):   
        self._load()     
        logpath=j.system.fs.joinPaths(j.dirs.logDir,"startup", "%s_%s_%s.log" % (self.jp.domain, self.jp.name,self.instance))        
        return logpath

    @deps
    def getTCPPorts(self,deps=True, *args, **kwargs):
        self._load()
        ports=[]
        for process in self.getProcessDicts():
            for item in process["ports"]:
                if item not in ports:
                    ports.append(item)
        return ports        

    def _load(self,args={},*stdargs,**kwargs):
        if self._loaded==False:
            self.hrdpath="%s/apps/jpackage.%s.%s.%s.hrd"%(j.dirs.hrdDir,self.jp.domain,self.jp.name,self.instance)
            self.actionspath="%s/jpackage_actions/%s__%s__%s.py"%(j.dirs.baseDir,self.jp.domain,self.jp.name,self.instance)

            args.update(self.args)

            # source="%s/instance.hrd"%self.jp.metapath
            # if args!={} or (not j.system.fs.exists(path=self.hrdpath) and j.system.fs.exists(path=source)):
            #     j.do.copyFile(source,self.hrdpath)
            # else:
            #     if not j.system.fs.exists(path=source):
            #         j.do.writeFile(self.hrdpath,"")                

            source="%s/actions.py"%self.jp.metapath
            j.do.copyFile(source,self.actionspath)
            
            args["jp.name"]=self.jp.name
            args["jp.domain"]=self.jp.domain
            args["jp.instance"]=self.instance

            hrd0=j.core.hrd.get("%s/instance.hrd"%self.jp.metapath)

            # orghrd=j.core.hrd.get(self.jp.hrdpath_main)
            self.hrd=j.core.hrd.get(self.hrdpath,args=args,templates=["%s/instance.hrd"%self.jp.metapath,"%s/jp.hrd"%self.jp.metapath])
            
            self.hrd.save()

            self.hrd.applyOnFile(self.actionspath, additionalArgs=args)
            j.application.config.applyOnFile(self.actionspath, additionalArgs=args)
            j.application.config.applyOnFile(self.hrdpath, additionalArgs=args)

            self.hrd=j.core.hrd.get(self.hrdpath)

            modulename="%s.%s.%s"%(self.jp.domain,self.jp.name,self.instance)
            mod = imp.load_source(modulename, self.actionspath)
            self.actions=mod.Actions()
            self.actions.jp_instance=self
            self._loaded=True

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
            if depth.lower()=="all":
                depth=None
            else:
                depth=int(depth)

        login = j.application.config.get("whoami.git.login").strip()
        passwd = j.application.config.get("whoami.git.passwd").strip()

        if login:
            dest=j.do.pullGitRepo(url=url, login=login, passwd=passwd, depth=depth, branch=branch,dest=dest)
        else:
            dest=j.do.pullGitRepo(url=url, login=login, passwd=passwd, depth=depth, branch=branch,revision=revision,dest=dest)  
        self._reposDone[url]=dest
        return dest      

    def getDependencies(self):
        res=[]
        for item in self.hrd.getListFromPrefix("dependencies"): 

            if isinstance(item,str):
                if item.strip()=="":
                    continue
                item2=item.strip()
                args={}
                item={}
                item["name"]=item2
                item["domain"]="jumpscale"
                item["instance"]="main"

            if "args" in item:
                if isinstance(item['args'], dict):
                    args = item['args']
                else:
                    argskey = item['args']
                    if self.hrd.exists(argskey):
                        args=self.hrd.getDict(argskey)
                    else:
                        args = {}
            else:
                args={}

            item['args']=args

            if "name" in item:
                name=item["name"]

            domain=""
            if "domain" in item:
                domain=item["domain"].strip()
            if domain=="":
                domain="jumpscale"

            instance="main"
            if "instance" in item:
                instance=item["instance"].strip()
            if instance=="":
                instance="main"

            jp=j.packages.get(name=name,domain=domain)            
            jp=jp.getInstance(instance)

            jp.args=args

            # if args!={}:
            #     jp._load()

            res.append(jp) 

        return res

    @deps
    def stop(self,args={},deps=True):
        self._load(args=args)
        self.actions.stop(**args)
        if not self.actions.check_down_local(**args):
            self.actions.halt(**args)

    @deps
    def build(self,args={},deps=True):
        self._load(args=args)
        for dep in self.getDependencies():
            if dep.jp.name not in j.packages._justinstalled:
                if 'args' in dep.__dict__:
                    dep.install(args=dep.args)
                else:
                    dep.install()
                j.packages._justinstalled.append(dep.jp.name)

        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            # print recipeitem
            #pull the required repo
            dest0=self._getRepo(recipeitem['url'],recipeitem=recipeitem)

        for recipeitem in self.hrd.getListFromPrefix("git.build"):
            # print recipeitem
            #pull the required repo
            name=recipeitem['url'].replace("https://","").replace("http://","").replace(".git","")
            dest0=self._getRepo(recipeitem['url'],recipeitem=recipeitem,dest="/opt/build/%s"%name)        

        self.actions.build(**args)

    @deps
    def start(self,args={},deps=True):
        self._load(args=args)
        self.actions.start(**args)

    @deps
    def restart(self,args={},deps=True):
        self._load(args=args)
        self.stop(args)
        self.start(args)

    def getProcessDicts(self,deps=True):
        self._load()
        res=[]
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

    def prepare(self,args={}):
        self._load(args=args)
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
            print "apt update"
            j.do.execute("apt-get update -y",dieOnNonZeroExitCode=False)

        if self.hrd.getBool("ubuntu.apt.upgrade",default=False):
            j.do.execute("apt-get upgrade -y",dieOnNonZeroExitCode=False)

        if self.hrd.exists("ubuntu.packages"):
            for jp in self.hrd.getList("ubuntu.packages"):
                if jp.strip()!="":
                    j.do.execute("apt-get install %s -f"%jp,dieOnNonZeroExitCode=False)     

        self.actions.prepare()  

    @deps
    def install(self,args={},start=True,deps=True):
        print "INSTALL:%s"%self
        
        self._load(args=args)
        docker=self.hrd.exists("docker.enable") and self.hrd.getBool("docker.enable")

        if j.packages.indocker or not docker:

            self.stop()

            for dep in self.getDependencies():
                if dep.jp.name not in j.packages._justinstalled:
                    if 'args' in dep.__dict__:
                        dep.install(args=dep.args)
                    else:
                        dep.install()
                    j.packages._justinstalled.append(dep.jp.name)
            
            self.prepare()
            #download

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
                    if link:
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


            self.actions.configure()

            self.start()

        else:
            #now bootstrap docker
            ports=""
            tcpports=self.hrd.getDict("docker.ports.tcp")
            for inn,outt in tcpports.items():
                ports+="%s:%s "%(inn,outt)
            ports=ports.strip()

            volsdict=self.hrd.getDict("docker.vols")
            vols=""
            for inn,outt in volsdict.items():
                vols+="%s:%s # "%(inn,outt)
            vols=vols.strip().strip("#").strip()

            if self.instance!="main":
                name="%s_%s"%(self.jp.name,self.instance)
            else:
                name="%s"%(self.jp.name)

            image=self.hrd.get("docker.base",default="despiegk/mc")

            mem=self.hrd.get("docker.mem",default="0")
            if mem.strip()=="":
                mem=0

            cpu=self.hrd.get("docker.cpu",default=None)
            if cpu.strip()=="":
                cpu=None

            ssh=self.hrd.get("docker.ssh",default=True)
            if ssh.strip()=="":
                ssh=True

            ns=self.hrd.get("docker.ns",default='8.8.8.8')
            if ns.strip()=="":
                ns='8.8.8.8'

            port=   j.tools.docker.create(name=name, ports=ports, vols=vols, volsro='', stdout=True, base=image, nameserver=ns, \
                replace=True, cpu=cpu, mem=0,jumpscale=True,ssh=ssh)

            self.hrd.set("docker.ssh.port",port)
            self.hrd.set("docker.name",name)
            self.hrd.save()

            hrdname="jpackage.%s.%s.%s.hrd"%(self.jp.domain,self.jp.name,self.instance)
            src="/%s/hrd/apps/%s"%(j.dirs.baseDir,hrdname)
            j.tools.docker.copy(name,src,src)
            j.tools.docker.run(name,"jpackage install -n %s -d %s"%(self.jp.name,self.jp.domain))

    @deps
    def publish(self,args={},deps=True):
        """
        check which repo's are used & push the info 
        this does not use the build repo's
        """
        self._load(args=args)
        self.actions.publish(**args)

    @deps
    def package(self,args={},deps=True):
        """
        """
        self._load(args)
        self.actions.package(**args)

    @deps
    def update(self,args={},deps=True):
        """
        - go over all related repo's & do an update
        - copy the files again
        - restart the app
        """
        self._load(args)
        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            # print recipeitem
            #pull the required repo
            dest0=self._getRepo(recipeitem['url'],recipeitem=recipeitem)

        for recipeitem in self.hrd.getListFromPrefix("git.build"):
            # print recipeitem
            #pull the required repo
            name=recipeitem['url'].replace("https://",""),replace("http://","").replace(".git","")
            dest="/opt/build/%s/%s"%name
            j.do.pullGitRepo(dest=dest,ignorelocalchanges=True)

        self.restart()

    @deps
    def resetstate(self,args={},deps=True):
        self._load(args)
        j.do.delete(self.hrdpath)
        j.do.delete(self.actionspath)
        j.do.delete(self.actionspath+"c")
        actionsdonepath="%s/cfg/actions/"%j.dirs.baseDir
        actioncat="jp_%s_%s"%(self.jp.domain,self.jp.name)
        j.do.delete("%s/%s.json"%(actionsdonepath,actioncat))


    @deps
    def reset(self,args={},deps=True):
        """
        - remove build repo's !!!
        - remove state of the app (same as resetstate) in jumpscale (the configuration info)
        - remove data of the app        
        """
        self._load(args)
        self._load(args=args)
        self.resetstate()
        #remove build repo's
        for recipeitem in self.hrd.getListFromPrefix("git.build"):
            name=recipeitem['url'].replace("https://","").replace("http://","").replace(".git","")
            dest="/opt/build/%s"%name
            j.do.delete(dest)
        
        self.actions.removedata(**args)

    @deps
    def uninstall(self,args={},deps=True):
        self._load(args)
        self.reset()
        self._load(args=args)
        self.actions.uninstall(**args)

    @deps
    def monitor(self,args={},deps=True):
        """
        do all monitor checks and return True if they all succeed
        """
        self._load(args=args)
        res=self.actions.check_up_local(**args)
        res=res and self.actions.monitor_local(**args)
        res=res and self.actions.monitor_remove(**args)
        return res

    @deps
    def iimport(self,url,args={},deps=True):
        self._load(args=args)
        self.actions.iimport(url,**args)

    @deps
    def export(self,args={},deps=True):        
        self._load(args=args)
        self.actions.export(url,**args)


    @deps
    def configure(self,args={},deps=True,restart=True):
        self._load(args=args)
        self.actions.configure(url,**args)
        if restart:
            self.restart()

    def __repr__(self):
        return "%-15s:%-15s:%s"%(self.jp.domain,self.jp.name,self.instance)

    def __str__(self):
        return self.__repr__()
