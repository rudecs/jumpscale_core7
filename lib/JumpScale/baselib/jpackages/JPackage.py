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

    def _load(self,args={}):
        if self._loaded==False:
            self.hrdpath="%s/apps/jpackage.%s.%s.%s.hrd"%(j.dirs.hrdDir,self.jp.domain,self.jp.name,self.instance)
            self.actionspath="%s/jpackage_actions/%s__%s__%s.py"%(j.dirs.baseDir,self.jp.domain,self.jp.name,self.instance)

            source="%s/instance.hrd"%self.jp.metapath
            if not j.system.fs.exists(path=self.hrdpath) and j.system.fs.exists(path=source):
                j.do.copyFile(source,self.hrdpath)

            source="%s/actions.py"%self.jp.metapath
            j.do.copyFile(source,self.actionspath)
            
            args["jp.name"]=self.jp.name
            args["jp.domain"]=self.jp.domain
            args["jp.instance"]=self.instance

            # orghrd=j.core.hrd.get(self.jp.hrdpath_main)
            self.hrd=j.core.hrd.get(self.hrdpath)

            self.hrd.applyTemplate(self.jp.hrdpath_main)
            self.hrd.save()

            self.hrd=j.core.hrd.get(self.hrdpath)

            j.application.config.applyOnFile(self.hrdpath, additionalArgs=args)

            hrd=j.packages.getHRD()

            hrd.applyOnFile(self.actionspath, additionalArgs=args)
            j.application.config.applyOnFile(self.actionspath, additionalArgs=args)

            modulename="%s.%s.%s"%(self.jp.domain,self.jp.name,self.instance)
            mod = imp.load_source(modulename, self.actionspath)
            self.actions=mod.Actions()
            self._loaded=True

    def install(self,args={}):
        self._load(args=args)
        self.actions.prepare(hrd=j.packages.hrd)
        #download

        for recipeitem in self.hrd.getListFromPrefix("git.export"):
            #pull the required repo
            if j.application.config.get("whoami.git.login")!="":
                dest=j.do.pullGitRepo(url=recipeitem['git'], login=j.application.config.get("whoami.git.login"), \
                    passwd=j.application.config.get("whoami.git.passwd"), depth=1, branch='master')
            else:
                dest=j.do.pullGitRepo(url=recipeitem['git'], login=None, passwd=None, depth=1, branch='master')
            src="%s/%s/"%(dest,recipeitem['source'])
            src=src.replace("//","/")
            dest=recipeitem['dest']            
            if recipeitem['link']=="true":
                j.do.symlink(src, dest)
            else:
                j.do.copyTree(src,dest)

            from IPython import embed
            print (100)
            embed()
            p        

        self.actions.configure(hrd=j.packages.hrd)
                

    def __repr__(self):
        return "%-15s:%-15s:%s"%(self.domain,self.name,self.instance)

    def __str__(self):
        return self.__repr__()

