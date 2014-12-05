from JumpScale import j
import imp
class JPackage():

    def __init__(self,domain="",name=""):
        self.name=name
        self.domain=domain
        self.hrd=None
        self.metapath=""
        self._loaded=False

        self.hrdpath=""
        self.hrdpath_main=""

    def _load(self):
        if self._loaded==False:
            # self.hrdpath="%s/apps/%s__%s"%(j.dirs.hrdDir,self.jp.domain,self.jp.name)
            self.hrdpath="%s/apps/jpackage.%s.%s.hrd"%(j.dirs.hrdDir,self.domain,self.name)
            self.metapath="%s/%s"%(j.packages.domains[self.domain],self.name)
            self.hrdpath_main="%s/jp.hrd"%self.metapath

            #this is hrd for jpackage (for all instances)
            src="%s/app.hrd"%self.metapath
            if j.system.fs.exists(path=src):
                j.do.copyFile(src,self.hrdpath)

            dest="%s/actions.py"%self.metapath
            if not j.system.fs.exists(path=dest):
                templ="/opt/code/github/jumpscale/jumpscale_core7/lib/JumpScale/baselib/jpackages/templates/action.py"
                j.do.copyFile(templ,dest)
            args={}
            args["jp.name"]=self.name
            args["jp.domain"]=self.domain

            if j.system.fs.exists(path=self.hrdpath):
                j.application.config.applyOnFile(self.hrdpath,additionalArgs=args)            
                self.hrd=j.core.hrd.get(self.hrdpath_main)            

        self._loaded=True

    def getInstance(self,instance="main"):
        self._load()
        # if self.hrd.getInt("instances.maxnr",default=1)==1:
        #     instance="main"
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

    def getLogPath(self):        
        logpath=j.system.fs.joinPaths(j.dirs.logDir,"startup", "%s_%s_%s.log" % (self.jp.domain, self.jp.name,self.instance))        
        return logpath

    def getTCPPorts(self):
        ports=self.hrd.getList("process.ports")
        ports=[int(item) for item in ports if str(item).strip()!=""]
        return ports        

    def _load(self,args={}):
        if self._loaded==False:
            self.hrdpath="%s/apps/jpackage.%s.%s.%s.hrd"%(j.dirs.hrdDir,self.jp.domain,self.jp.name,self.instance)
            self.actionspath="%s/jpackage_actions/%s__%s__%s.py"%(j.dirs.baseDir,self.jp.domain,self.jp.name,self.instance)

            source="%s/instance.hrd"%self.jp.metapath
            if args!={} or (not j.system.fs.exists(path=self.hrdpath) and j.system.fs.exists(path=source)):
                j.do.copyFile(source,self.hrdpath)
            else:
                if not j.system.fs.exists(path=source):
                    j.do.writeFile(self.hrdpath,"")                

            source="%s/actions.py"%self.jp.metapath
            j.do.copyFile(source,self.actionspath)
            
            args["jp.name"]=self.jp.name
            args["jp.domain"]=self.jp.domain
            args["jp.instance"]=self.instance


            # orghrd=j.core.hrd.get(self.jp.hrdpath_main)
            self.hrd=j.core.hrd.get(self.hrdpath,args=args)

            self.hrd.applyTemplate(self.jp.hrdpath_main)

            self.hrd.set("jp.name",self.jp.name)
            self.hrd.set("jp.domain",self.jp.domain)
            self.hrd.set("jp.instance",self.instance)

            self.hrd.save()

            self.hrd=j.core.hrd.get(self.hrdpath)

            j.application.config.applyOnFile(self.hrdpath, additionalArgs=args)

            self.hrd=j.core.hrd.get(self.hrdpath)

            hrd=j.packages.getHRD(reload=True)

            hrd.applyOnFile(self.actionspath, additionalArgs=args)
            self.hrd.applyOnFile(self.actionspath, additionalArgs=args)
            j.application.config.applyOnFile(self.actionspath, additionalArgs=args)

            modulename="%s.%s.%s"%(self.jp.domain,self.jp.name,self.instance)
            mod = imp.load_source(modulename, self.actionspath)
            self.actions=mod.Actions()
            self.actions.jp_instance=self
            self._loaded=True

    def _getRepo(self,url):
        if url in self._reposDone:
            return self._reposDone[url]
        if j.application.config.get("whoami.git.login")!="":
            dest=j.do.pullGitRepo(url=url, login=j.application.config.get("whoami.git.login"), \
                passwd=j.application.config.get("whoami.git.passwd"), depth=1, branch='master')
        else:
            dest=j.do.pullGitRepo(url=url, login=None, passwd=None, depth=1, branch='master')  
        self._reposDone[url]=dest
        return dest      


    def getDependencies(self):
        res=[]
        for item in self.hrd.getList("dependencies"): 
            jp=j.packages.get(name=item)
            jp=jp.getInstance("main")
            res.append(jp) 
        return res

    def stop(self,args={}):
        self._load(args=args)
        self.actions.stop(**args)
        if not self.actions.check_down_local(**args):
            self.actions.halt(**args)

    def start(self,args={}):
        self._load(args=args)
        self.actions.start(**args)

    def restart(self,args={}):
        self.stop(args)
        self.start(args)

    def install(self,args={},start=True):
        
        self._load(args=args)

        for dep in self.getDependencies():
            if dep.jp.name not in j.packages._justinstalled:
                dep.install()
                j.packages._justinstalled.append(dep.jp.name)


        self.actions.prepare()
        #download

        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            
            #pull the required repo
            dest0=self._getRepo(recipeitem['url'])
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
                if link:
                    j.system.fs.createDir(j.do.getParent(dest))
                    j.do.symlink(src, dest)
                else:
                    if j.system.fs.exists(path=dest):
                        if "overwrite" in recipeitem:
                            if recipeitem["overwrite"].lower()=="false":
                                continue
                            else:
                                j.do.delete(dest)
                                j.system.fs.createDir(dest)
                                j.do.copyTree(src,dest)
                    else:
                        j.do.copyTree(src,dest)

        self.actions.configure()

        if start:
            self.actions.start()


    def __repr__(self):
        return "%-15s:%-15s:%s"%(self.jp.domain,self.jp.name,self.instance)

    def __str__(self):
        return self.__repr__()
