import copy
import time
import inspect

from JumpScale import j

from .JPackageStateObject import JPackageStateObject
#from JumpScale.core.sync.Sync import SyncLocal
from .ActionManager import ActionManager

from .CodeManagementRecipe import CodeManagementRecipe
from JumpScale.core.system.fs import FileLock

def JPLock(func):
    def wrapper(self, *args, **kwargs):
        lockname = "jp_%s_%s" % (self.domain, self.name)
        with FileLock(lockname, True):
            return func(self, *args, **kwargs)
    return wrapper

class JPackageObject():
    """
    Data representation of a JPackage, should contain all information contained in the jpackages.cfg
    """

    def __init__(self, domain, name, version,instance=0):
        """
        Initialization of the JPackage

        @param domain:  The domain that the JPackage belongs to, can be a string or the DomainObject4
        @param name:    The name of the JPackage
        @param version: The version of the JPackage
        """

        self.supportedPlatforms=[]
        self.domain=domain
        self.name=name
        self.version=version
        self.instance=None
        self.supportedPlatforms=[]
        self.tags=[]
        self.description=""


        #checks on correctness of the parameters
        if not domain:
            raise ValueError('The domain parameter cannot be empty or None')
        if not name:
            raise ValueError('The name parameter cannot be empty or None')
        if not version:
            raise ValueError('The version parameter cannot be empty or None')

        self.buildNr=-1
        self.taskletsChecksum=""    
        
        self.configchanged=False
              
        self.metadata=None

        self.dependencies=[] #key = domain_packagename
        self.dependenciesNames={}

        self.hrd=None
        self.hrd_instance=None

        self.actions=None
                
        self._clean()
        self._init()

        ########
        #create defaults for new jpackages
        hrdpath=j.system.fs.joinPaths(self.getPathMetadata(),"hrd","main.hrd")
        if not j.system.fs.exists(hrdpath):
            self.init()

        ########
        #LOAD INFO FROM REPO       
        self.hrd=j.core.hrd.getHRD(hrdpath)

        self._clear()
        self.buildNr = self.hrd.getInt("jp.buildNr")

        if self.hrd.exists("jp.process.tcpports"):
            self.hrd.delete("jp.process.tcpports")
        if self.hrd.exists("jp.process.startuptime"):
            self.hrd.delete("jp.process.startuptime")

        self.export = self.hrd.getBool("jp.export")
        self.autobuild = self.hrd.getBool("jp.autobuild")
        self.taskletsChecksum = self.hrd.getStr("jp.taskletschecksum")

        self.descrChecksum = self.hrd.getStr("jp.descrchecksum",default="")

        self.hrdChecksum = self.hrd.getStr("jp.hrdchecksum",default="")

        self.supportedPlatforms = self.hrd.getList("jp.supportedplatforms")

        j.packages.getDomainObject(self.domain)

        self.blobstorRemote = None
        self.blobstorLocal = None

        self.actions = None

        self._getState()
        self.debug=self.state.debugMode

        if (self.debug==False or self.debug==0) and self.hrd.exists("jp.debug"):
            if int(self.hrd.getStr("jp.debug"))==1:
                self.debug=1
            #DO NOT SET 0, 0 means we don't count the stat from the hrd
      
        key="%s_%s_%s" % (self.domain,self.name,self.version)
        self._activeblobfolder = j.system.fs.joinPaths(j.dirs.cfgDir, "jpackages", "state", key)
        self._blobfolder = j.system.fs.joinPaths(self.getPathMetadata(),"files")


        # print "**JP:%s"%self
        self._loaded=False

    def log(self,msg,category="",level=5):
        if level<j.packages.loglevel+1 and j.packages.logenable:
            j.packages.log("%s:%s"%(self,msg),category=category,level=level)        

    # @JPLock
    def _init(self):
        #create defaults for new jpackages
        hrddir=j.system.fs.joinPaths(self.getPathMetadata(),"hrd")

        #define templates path
        extpath=inspect.getfile(self.__init__)
        extpath=j.system.fs.getDirName(extpath)
        src=j.system.fs.joinPaths(extpath,"templates")        

        #this is to check if metadata in jpackage dir (on repo) is complete
        if not j.system.fs.exists(hrddir):
            if self.hrd==None:
                content="jp.domain=%s\n"%self.domain
                content+="jp.name=%s\n"%self.name
                content+="jp.version=%s\n"%self.version
                self.hrd=j.core.hrd.getHRD(content=content)

            j.system.fs.copyDirTree(src,self.getPathMetadata(), overwriteFiles=False) #do never put this on true

        j.system.fs.copyDirTree(src+"/actions/",self.getPathMetadata()+"/actions/", overwriteFiles=False)

        #for easy development, overwrite specific implementations
        #j.system.fs.copyFile(src+"/actions/process.depcheck.py",self.getPathMetadata()+"/actions/process.depcheck.py")

        self.hrd=j.core.hrd.getHRD(path=j.system.fs.joinPaths(hrddir,"main.hrd"))

        if self.hrd.getStr("jp.domain") != self.domain:
            try:
                self.hrd.set("jp.domain",self.domain)
            except:
                print("WARNING: domain in jpackage is not same as name of directory.")
        if self.hrd.getStr("jp.name") != self.name:
            try:
                self.hrd.set("jp.name",self.name)
            except:
                print("WARNING: name in jpackage is not same as name of directory.")
            
        if self.hrd.getStr("jp.version") != self.version:                
            try:
                self.hrd.set("jp.version",self.version)
            except:
                print("WARNING: version in jpackage is not same as name of directory.")

        descr=self.hrd.getStr("jp.description")
        if descr != False and descr != "":
            self.description=descr
        if descr != self.description:                
            self.hrd.set("jp.description",self.description)                      

        self.supportedPlatforms=self.hrd.getList("jp.supportedplatforms")

        if self.supportedPlatforms==[]:
            self._raiseError("supported platforms cannot be empty")

        j.system.fs.createDir(j.system.fs.joinPaths(self.getPathMetadata(),"uploadhistory"))
        j.system.fs.createDir(j.system.fs.joinPaths(self.getPathMetadata(),"files"))

        for platform in self.supportedPlatforms:
            j.system.fs.createDir(self.getPathFilesPlatform(platform))
  
    def _clean(self):
        for item in [".quarantine",".tmb"]:
        # for item in [".quarantine",".tmb",'actions/code.getRecipe']:
            path=j.system.fs.joinPaths(self.getPathMetadata(),item)
            # print "remove:%s"%path
            j.system.fs.removeDirTree(path)
        for item in [".quarantine",".tmb"]:
            path=j.system.fs.joinPaths(self.getPathFiles(),item)
            j.system.fs.removeDirTree(path)
            # print "remove:%s"%path

        # j.system.fs.remove("%s/actions/install.download.py"%self.getPathMetadata())

    # @JPLock
    def load(self,instance=None,force=False,hrddata={},findDefaultInstance=True):

        if self._loaded and force==False and (instance is None or instance == self.instance):
            return

        #TRY AND FIND INSTANCE
        if instance==None and findDefaultInstance:
            root=j.system.fs.joinPaths(j.dirs.packageDir, "instance", self.domain,self.name)
            if j.system.fs.exists(path=root):
                instanceNames=j.system.fs.listDirsInDir(root,False,True)
                if len(instanceNames)==1:
                    self.instance=instanceNames[0]
        else:
            if instance != None:
                root=j.system.fs.joinPaths(j.dirs.packageDir, "instance", self.domain,self.name,instance)
                if not j.system.fs.exists(path=root):
                    j.events.inputerror_critical("Could not find instance '%s' for jpackage %s"%(instance,self),"jpackage.init")
                self.instance=instance

        if hrddata != {}:
            self._installActiveHrd(hrddata=hrddata)

        hrdinstancepath = j.system.fs.joinPaths(self.getPathInstance(),"hrdinstance")
        if j.system.fs.exists(hrdinstancepath):
            # j.events.inputerror_critical("Cannot load jpackage:%s could not find an instance"%self)
            self.hrd_instance=j.core.hrd.getHRD(hrdinstancepath)
        self.actions = ActionManager(self)

        #WHY WOULD THIS BE NEEDED?
        #j.application.loadConfig()


        self.loadBlobStores()

        # print "loadactionsdone:%s"%self

        # ######CHECK IF JP ALREADY INSTALLED 
        # if self.state.lastinstalledbuildnr>=0:
        #     #means jp is installed on system
        #     #because was already installed make sure we create active instance if we can't find the active path yet

        #     #get rid of past
        #     oldpath=j.system.fs.joinPaths(j.dirs.packageDir, "instance", self.domain,self.name,self.version)
        #     if j.system.fs.exists(path=oldpath):
        #         j.system.fs.removeDirTree(oldpath)

        #     root=j.system.fs.joinPaths(j.dirs.packageDir, "instance", self.domain,self.name)
        #     if not j.system.fs.exists(path=root) or len(j.system.fs.listDirsInDir(root,False,True))==0:
                
        #         #this is to allow system to keep on running when upgrading from old situation
        #         self.instance=0
        #         hrdinstancepath=j.system.fs.joinPaths(self.getPathInstance(),"hrdinstance")  
        #         j.system.fs.createDir(hrdinstancepath)
        #         self.copyMetadataToActive()

        self._loaded=True
        return self

    # @JPLock
    def getCodeMgmtRecipe(self):
        self._init()
        self.load()

        hrdpath=j.system.fs.joinPaths(self.getPathMetadata(),"hrd","code.hrd")
        if not j.system.fs.exists(path=hrdpath):
            self.init()
        recipepath=j.system.fs.joinPaths(self.getPathMetadata(),"coderecipe.cfg")
        if not j.system.fs.exists(path=recipepath):
            self.init()
        return CodeManagementRecipe(hrdpath,recipepath,jp=self)

    def _installActiveHrd(self,hrddata={}):
        """
        match hrd templates with active ones, add entries where needed
        """
        #THE ACTIVATE ONES
        hrdtemplatesPath=j.system.fs.joinPaths(self.getPathMetadata(),"hrdactive")
        for item in j.system.fs.listFilesInDir(hrdtemplatesPath):
            base=j.system.fs.getBaseName(item)
            if base[0] != "_":
                templ=j.system.fs.fileGetContents(item)                
                actbasepath=j.system.fs.joinPaths(j.dirs.hrdDir,base)
                if not j.system.fs.exists(actbasepath):
                    #means there is no hrd, put empty file
                    self.log("did not find active hrd for %s, will now put there"%actbasepath,category="init")
                    j.system.fs.writeFile(actbasepath,"")
                hrd=j.core.hrd.getHRD(actbasepath)
                hrd.checkValidity(templ,hrddata=hrddata)

        #########
        #now load the ones which are specific per instance
        hrdinstancepath=j.system.fs.joinPaths(self.getPathInstance(),"hrdinstance")  
        j.system.fs.createDir(hrdinstancepath)        
        hrdtemplatesPath=j.system.fs.joinPaths(self.getPathMetadata(),"hrdinstance")
        if j.system.fs.exists(path=hrdtemplatesPath):
            for item in j.system.fs.listFilesInDir(hrdtemplatesPath):
                base=j.system.fs.getBaseName(item)
                if base[0] != "_":
                    templ=j.system.fs.fileGetContents(item)                
                    actbasepath=j.system.fs.joinPaths(self.getPathInstance(),"hrdinstance",base)
                    if not j.system.fs.exists(actbasepath):
                        #means there is no hrd, put empty file
                        self.log("did not find instance hrd for %s, will now put there"%actbasepath,category="init")
                        j.system.fs.writeFile(actbasepath,"")
                    hrd=j.core.hrd.getHRD(actbasepath)
                    hrd.checkValidity(templ,hrddata=hrddata)

        j.application.loadConfig() #makes sure hrd gets reloaded to application.config object

    # @JPLock
    def _copyMetadataToActive(self,hrddata={}):
        
        instancepathactions=j.system.fs.joinPaths(self.getPathInstance(),"actions")

        if j.system.fs.isDir(instancepathactions):
            j.system.fs.removeDirTree(instancepathactions)
        j.system.fs.createDir(instancepathactions)
        
        sourcepath=self.getPathMetadata()
        for actionname in j.packages.getActionNamesInstance():
            srcpath=j.system.fs.joinPaths(sourcepath,"actions","%s.py"%actionname)
            destpath=j.system.fs.joinPaths(instancepathactions,"%s.py"%actionname)
            j.system.fs.copyFile(srcpath,destpath)

        self._installActiveHrd(hrddata=hrddata)
        hrdinstancepath=j.system.fs.joinPaths(self.getPathInstance(),"hrdinstance") 

        self.hrd_instance=j.core.hrd.getHRD(hrdinstancepath)

        dir2apply=self.getPathInstance()

        #apply apackage hrd data on actions active
        self.hrd_instance.applyOnDir(dir2apply) 
        #make sure params are filled in in actions dir
        self.hrd.applyOnDir(dir2apply) 
        #apply hrd config from system on actions active
        j.application.config.applyOnDir(dir2apply)

        additionalArgs={}
        additionalArgs["jp_instance"]=self.instance
        additionalArgs["jp_name"]=self.name
        additionalArgs["jp_domain"]=self.domain
        additionalArgs["jp_version"]=self.version

        j.dirs.replaceFilesDirVars(dir2apply,additionalArgs=additionalArgs)

    def loadBlobStores(self):
        self._init()
        do = j.packages.getDomainObject(self.domain)
        if do.blobstorremote.strip() != "":
            self.blobstorRemote = j.clients.blobstor.get(do.blobstorremote)

        if do.blobstorlocal.strip() != "":
            self.blobstorLocal = j.clients.blobstor.get(do.blobstorlocal)

        if self.blobstorRemote ==None or   self.blobstorLocal==None:
            self._raiseError("DEBUG NOW blobstorremote or blobstorlocal needs to be available")

    def getAppPath(self):
        path = self.hrd.getStr("jp.app.path")
        if path is None:
            j.events.inputerror_critical("Could not find 'jp.app.path' in main hrd of jpackage:%s"%jp)
        path = j.dirs.replaceTxtDirVars(path)
        if path is None:
            j.events.inputerror_critical("Could not find data for 'jp.app.path' in main hrd of jpackage:%s"%jp)
        return self.hrd_instance.applyOnContent(path)
        
    def getDebugMode(self):
        return self.state.debugMode

    def getDebugModeInJpackage(self):
        if self.hrd.exists("jp.debug"):
            if int(self.hrd.getStr("jp.debug"))==1:
                return True
        return False

    def setDebugMode(self,dependencies=False):
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.setDebugMode(dependencies=False)

        self.state.setDebugMode()
        recipe=self.getCodeMgmtRecipe()
        recipe.addToProtectedDirs()

        self.load(findDefaultInstance=False)
        self.log("set debug mode",category="init")

    def setDebugModeInJpackage(self,dependencies=False): 
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.setDebugModeInJpackage(dependencies=False)
        self.hrd.set("jp.debug",1)
        self.load(findDefaultInstance=False)
        self.log("set debug mode in jpackage",category="init")

    def removeDebugModeInJpackage(self,dependencies=False):
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.removeDebugModeInJpackage(dependencies=False)
        if self.hrd.exists("jp.debug"):
            self.hrd.set("jp.debug",0)
        self.load(findDefaultInstance=False)
        self.log("remove debug mode in jpackage",category="init")        

    def removeDebugMode(self,dependencies=False):

        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.removeDebugMode(dependencies=False)

        recipe=self.getCodeMgmtRecipe()
        recipe.removeFromProtectedDirs()

        self.state.setDebugMode(mode=0)
        self.log("remove debug mode",category="init")


###############################################################
############  MAIN OBJECT METHODS (DELETE, ...)  ##############
###############################################################

    @JPLock
    def delete(self):
        """
        Delete all metadata, files of the jpackages
        """
        # self._init()
        self.loadActions()
        if j.application.shellconfig.interactive:
            do = j.gui.dialog.askYesNo("Are you sure you want to remove %s_%s_%s, all metadata & files will be removed" % (self.domain, self.name, self.version))
        else:
            do = True
        if do:
            path = j.packages.getDataPath(self.domain, self.name, self.version)
            j.system.fs.removeDirTree(path)
            path = j.packages.getMetadataPath(self.domain, self.name,self.version)
            j.system.fs.removeDirTree(path)
            path = self.getPathActions(self.domain, self.name,self.instance)
            j.system.fs.removeDirTree(path)
            #@todo over ftp try to delete the targz file (less urgent), check with other quality levels to make sure we don't delete files we should not delete

    @JPLock
    def save(self, new=False):
        """
        Creates a new config file and saves the most important jpackages params in it

        @param new: True if we are saving a new Q-Package, used to ensure backwards compatibility
        @type new: boolean
        """      
        self.log('saving jpackages data to ' + self.getPathMetadata(),category="save")

        if self.buildNr == "":
            self._raiseError("buildNr cannot be empty")

        self.hrd.set("jp.buildNr",self.buildNr)        
        self.hrd.set("jp.export",self.export)
        self.hrd.set("jp.autobuild",self.autobuild)
        self.hrd.set("jp.taskletschecksum",self.taskletsChecksum)
        self.hrd.set("jp.hrdchecksum",self.hrdChecksum)
        self.hrd.set("jp.descrchecksum",self.descrChecksum)
        self.hrd.set("jp.supportedplatforms",self.supportedPlatforms)

        # for idx, dependency in enumerate(self.dependencies):
        #     self._addDependencyToHRD(idx, dependency.domain, dependency.name,minversion=dependency.minversion,maxversion=dependency.maxversion)

    @JPLock
    def _addDependencyToHRD(self, idx, domain, name, minversion, maxversion):
        hrd = self.hrd
        basekey = 'jp.dependency.%s.%%s' % idx
        def setValue(name, value):
            hrd.set(basekey % name, value)

        setValue('domain', domain)
        setValue('name', name)
        setValue('minversion', minversion)
        setValue('maxversion', maxversion)

##################################################################################################
###################################  DEPENDENCY HANDLING  #######################################
##################################################################################################


    def loadDependencies(self, errorIfNotFound=True):
        
        if self.dependencies==[]:

            ids = set()
            for key in self.hrd.prefix('jp.dependency'):
                try:
                    ids.add(int(key.split('.')[2]))
                except Exception:
                    self._raiseError("Error in jpackage hrd:%s"%self)

            ids = list(ids)
            ids.sort(reverse=True)
            #walk over found id's
            for id in ids:
                key="jp.dependency.%s.%%s"%id
                if not self.hrd.exists(key % 'minversion'):
                    self.hrd.set(key % 'minversion',"")
                if not self.hrd.exists(key % 'maxversion'):
                    self.hrd.set(key % 'maxversion',"")
                   
                name=self.hrd.getStr(key % 'name')
                domain=self.hrd.getStr(key % 'domain')
                minversion=self.hrd.getStr(key % 'minversion')
                maxversion=self.hrd.getStr(key % 'maxversion')

                deppack=j.packages.findNewest(domain,name,\
                    minversion=minversion,maxversion=maxversion,returnNoneIfNotFound=not(errorIfNotFound)) #,platform=j.system.platformtype.myplatformdeppack.loadDependencies()

                if errorIfNotFound == False and deppack == None:
                    continue

                deppackKey="%s__%s"%(deppack.domain,deppack.name)
                self.dependenciesNames[deppackKey]=deppack

                #now deps of deps
                deppack.loadDependencies()
                self.dependencies.append(deppack)
                for deppack2 in reversed(deppack.dependencies):
                    if deppack2 in self.dependencies:
                        self.dependencies.remove(deppack2)
                    self.dependencies.append(deppack2)
                    deppackKey2="%s__%s"%(deppack2.domain,deppack2.name)
                    self.dependenciesNames[deppackKey2]=deppack2
            self.dependencies.reverse()

    def addDependency(self, domain, name, supportedplatforms, minversion, maxversion, dependencytype):
        dep = DependencyDef4()
        dep.name = name
        dep.domain = domain
        dep.minversion = minversion
        dep.maxversion = maxversion
        # dep.supportedPlatforms = supportedplatforms
        # dep.dependencytype = j.enumerators.DependencyType4.getByName(dependencytype)
        # self.dependencyDefs.append(dep)
        self.save()
        self.dependencies=[]
        self.loadDependencies()
        

#############################################################################
####################################  GETS  #################################
#############################################################################

    def getIsPreparedForUpdatingFiles(self):
        """
        Return true if package has been prepared
        """
        prepared = self.state.prepared
        if prepared == 1:
            return True
        return False

    def getKey(self):
        return "%s|%s|%s"%(self.domain,self.name,self.version)

    def getDependingInstalledPackages(self, recursive=False, errorIfNotFound=True):
        """
        Return the packages that are dependent on this packages and installed on this machine
        This is a heavy operation and might take some time
        """
        ##self.assertAccessable()
        if errorIfNotFound and self.getDependingPackages(recursive=recursive, errorIfNotFound=errorIfNotFound) == None:
            self._raiseError("No depending packages present")
        [p for p in self.getDependingPackages(recursive=recursive, errorIfNotFound=errorIfNotFound) if p.isInstalled()]

    def getDependingPackages(self, recursive=False, errorIfNotFound=True):
        """
        Return the packages that are dependent on this package
        This is a heavy operation and might take some time
        """
        return [p for p in j.packages.getJPackageObjects() if self in p.getDependencies(errorIfNotFound)]

    def _getState(self):
        ##self.assertAccessable()
        """
        from dir get [qbase]/cfg/jpackages/state/$jpackagesdomain_$jpackagesname_$jpackagesversion.state
        is a inifile with following variables
        * lastinstalledbuildnr
        * lastaction
        * lasttag
        * lastactiontime  epoch of last time an action was done
        * currentaction  ("" if no action current)
        * currenttag ("" if no action current)
        * lastexpandedbuildNr  (means expanded from tgz into jpackages dir)
        @return a JpackageStateObject
        """
        self.state=JPackageStateObject(self)

    def getVersionAsInt(self):
        """
        Translate string version representation to a number
        """
        ##self.assertAccessable()
        #@todo
        version = self.version
        return float(version)

    def getPathInstance(self):
        """
        Return absolute pathname of the package's metadatapath
        """
        return j.packages.getJPActiveInstancePath(self.domain, self.name, self.instance)

    def getPathMetadata(self):
        """
        Return absolute pathname of the package's metadatapath active instance
        """
        return j.packages.getMetadataPath(self.domain, self.name, self.version)

    def getPathFiles(self):
        """
        Return absolute pathname of the jpackages's filespath
        """
        ##self.assertAccessable()
        return j.packages.getDataPath(self.domain, self.name, self.version)

    def getPathFilesPlatform(self, platform=None):
        """
        Return absolute pathname of the jpackages's filespath
        if not given then will be: j.system.platformtype
        """
        ##self.assertAccessable()
        if platform==None:
            platform=j.system.platformtype.myplatform
        platform=self._getPackageInteractive(platform)
        path =  j.system.fs.joinPaths(self.getPathFiles(), str(platform))
        return path

    def getPathFilesPlatformForSubDir(self, subdir):
        """
        Return absolute pathnames of the jpackages's filespath for platform or parent of platform if it does not exist in lowest level
        if platform not given then will be: j.system.platformtype
        the subdir will be used to check upon if found in one of the dirs, if never found will raise error
        all matching results are returned
        """
        result=[]
        for possibleplatform in j.system.platformtype.getMyRelevantPlatforms():
            # print platform
            path =  j.system.fs.joinPaths(self.getPathFiles(), possibleplatform,subdir)
            #print path
            if j.system.fs.exists(path):
                result.append(path)
        if len(result)==0:
            self._raiseError("Could not find subdir %s in files dirs for '%s'"%(subdir,self))
        return result

    def getPathSourceCode(self):
        """
        Return absolute path to where this package's source can be extracted to
        """
        raise NotImplementedError()
        #return j.system.fs.joinPaths(j.dirs.varDir, 'src', self.name, self.version)

    def getHighestInstalledBuildNr(self):
        """
        Return the latetst installed buildnumber
        """
        ##self.assertAccessable()
        return self.state.lastinstalledbuildnr

    def buildNrIncrement(self):
        buildNr=0
        for ql in self.getQualityLevels():
            path=self.getMetadataPathQualityLevel(ql)
            if path != None:
                path= j.system.fs.joinPaths(path,"hrd","main.hrd")
                buildNr2=j.core.hrd.getHRD(path).getInt("jp.buildNr")
                if buildNr2>buildNr:
                    buildNr=buildNr2
        
        buildNr+=1
        self.buildNr=buildNr
        self.save()
        return self.buildNr
            
    def getMetadataPathQualityLevel(self,ql):
        path=j.system.fs.joinPaths(j.dirs.packageDirMD, self.domain)
        if not j.system.fs.isLink(path):
            self._raiseError("%s needs to be link"%path)
        jpackagesdir=j.system.fs.getParent(j.system.fs.readlink(path))
        path= j.system.fs.joinPaths(jpackagesdir,ql,self.name,self.version)
        if not j.system.fs.exists(path=path):
            return None
        return path

    def getQualityLevels(self):
        path=j.system.fs.joinPaths(j.dirs.packageDirMD, self.domain)
        if not j.system.fs.isLink(path):
            self._raiseError("%s needs to be link"%path)
        jpackageconfig = j.config.getConfig('sources', 'jpackages')
        ql = jpackageconfig[self.domain].get('qualitylevel', [])
        return [ql] if not isinstance(ql, list) else ql

    def getBrokenDependencies(self, platform=None):
        """
        Return a list of dependencies that cannot be resolved
        """
        platform=self._getPackageInteractive(platform)
        broken = []
        for dep in self.dependencies:   # go over my dependencies
                                        # Do this without try catch
                                        # pass boolean to findnewest that it should return None instead of fail
            try:
                j.packages.findNewest(domain=dep.domain, name=dep.name, minversion=dep.minversion, maxversion=dep.maxversion, platform=platform)
            except Exception as e:
                print(str(e))
                broken.append(dep)
        return broken

    def getDependencies(self, errorIfNotFound=True):
        """
        Return the dependencies for the JPackage
        """
        self.loadDependencies(errorIfNotFound)
        return self.dependencies

    def getInstanceNames(self):
        root=j.system.fs.joinPaths(j.dirs.packageDir, "instance", self.domain,self.name)
        if j.system.fs.exists(root):
            return j.system.fs.listDirsInDir(root,False,True)
        return list()

    def _getPackageInteractive(self,platform):

        if platform == None and len(self.supportedPlatforms) == 1:
            platform = self.supportedPlatforms[0]
        
        if platform==None and j.application.shellconfig.interactive:
            platform = j.gui.dialog.askChoice("Select platform.",self.supportedPlatforms ,str(None))
        
        if platform==None:
            platform=None
        return platform

    def _copyBlobInfo(self):
        j.system.fs.copyDirTree(self._blobfolder, self._activeblobfolder)

    def getBlobInfo(self,platform,ttype,active=False):
        """
        @return blobkey,[[md5,path],...]
        """
        blobfolder = self._blobfolder if not active else self._activeblobfolder
        path=j.system.fs.joinPaths(blobfolder,"%s___%s.info"%(platform,ttype))
        if j.system.fs.exists(path):
            content=j.system.fs.fileGetContents(path)
            splitted=content.split("\n")
            key=splitted[0].strip()
            result=[]
            splitted=splitted[1:]
            for item in splitted:
                item=item.strip()
                if item=="":
                    continue
                result.append([item.strip() for item in item.split("|")])
            return key,result
        else:
            return None,[]

    def getBlobItemPaths(self,platform,ttype,blobitempath):
        """
        translates the item as shown in the blobinfo to the corresponding paths (jpackageFilesPath,destpathOnSystem)
        """
        platform=platform.lower().strip()
        ttype=ttype.lower().strip()
        ptype = ttype
        if ptype.find("cr_")==0:
            ptype=ttype[3:]

        filespath=j.system.fs.joinPaths(self.getPathFiles(),platform,ttype,blobitempath)
        systemdest = j.packages.getTypePath(ptype, blobitempath,jp=self)
        return (filespath,systemdest)

    @JPLock
    def getBlobPlatformTypes(self, active=False):
        """
        @return [[platform,ttype],...]
        """
        #@TODO this is plain wrong !!!!
        result=[]
        path = self._blobfolder if not active else self._activeblobfolder
        if not j.system.fs.exists(path=path):
            if not active:
                self.init()
            else:
                return result
        infofiles=[j.system.fs.getBaseName(item) for item in j.system.fs.listFilesInDir(path,False) if item.find("___") != -1]
        for item in infofiles:
            platform,ttype=item.split("___")
            ttype=ttype.replace(".info","")
            if ttype != "":
                result.append([platform,ttype])        
        return result

    def getCodeLocationsFromRecipe(self):
        items=[]
        for item in self.getCodeMgmtRecipe().items:
            item.systemdest
            path=item.getSource()
            if j.system.fs.isFile(path):
                path=j.system.fs.getDirName(path)
            items.append(path)
            
        items.sort()
        result=[]
        previtem="willnotfindthis"
        for x in range(len(items)):                
            item=items[x]
            # print "previtem:%s now:%s"%(previtem,item)
            if not item.find(previtem)==0:
                previtem=item
                if item not in result:
                    # print "append"
                    result.append(item) 
        
        return result

    def _getPlatformDirsToCopy(self):
        """
        Return a list of platform related directories to be copied in sandbox
        """

        platformDirs = list()
        platform = j.system.platformtype

        _jpackagesDir = self.getPathFiles()

        platformSpecificDir = j.system.fs.joinPaths(_jpackagesDir, str(platform), '')

        if j.system.fs.isDir(platformSpecificDir):
            platformDirs.append(platformSpecificDir)

        genericDir = j.system.fs.joinPaths(_jpackagesDir, 'generic', '')

        if j.system.fs.isDir(genericDir):
            platformDirs.append(genericDir)

        if platform.isUnix():
            unixDir = j.system.fs.joinPaths(_jpackagesDir, 'unix', '')
            if j.system.fs.isDir(unixDir):
                platformDirs.append(unixDir)

            if platform.isSolaris():
                sourceDir = j.system.fs.joinPaths(_jpackagesDir, 'solaris', '')
            elif platform.isLinux():
                sourceDir = j.system.fs.joinPaths(_jpackagesDir, 'linux', '')
            elif platform.isDarwin():
                sourceDir = j.system.fs.joinPaths(_jpackagesDir, 'darwin', '')

        elif platform.isWindows():
            sourceDir = j.system.fs.joinPaths(_jpackagesDir, 'win', '')

        if j.system.fs.isDir(sourceDir):
            if not str(sourceDir) in platformDirs:
                platformDirs.append(sourceDir)

        return platformDirs

#############################################################################
################################  CHECKS  ###################################
#############################################################################

    def hasModifiedFiles(self):
        """
        Check if files are modified in the JPackage files
        """
        ##self.assertAccessable()
        if self.state.prepared == 1:
            return True
        return False

    def hasModifiedMetaData(self):
        """
        Check if files are modified in the JPackage metadata
        """
        ##self.assertAccessable()
        return self in j.packages.getDomainObject(self.domain).getJPackageTuplesWithModifiedMetadata()

    def isInstalled(self, instance=None,checkAndDie=False,hrdcheck=True):
        """
        Check if the JPackage is installed
        """

        installed = self.state.lastinstalledbuildnr != -1

        if hrdcheck:
            if instance != None:
                hrdinstancepath = j.packages.getJPActiveInstancePath(self.domain, self.name, instance)
            elif self.instance is None:
                instances = self.getInstanceNames()
                if instances:
                    hrdinstancepath = j.packages.getJPActiveInstancePath(self.domain, self.name, instances[0])
                else:
                    hrdinstancepath = None
            else:
                hrdinstancepath = self.getPathInstance()
            if hrdinstancepath is not None and not j.system.fs.exists(path=hrdinstancepath):
                installed=False

        if checkAndDie and installed==False:
            j.events.opserror_critical("Jpackage %s is not installed, cannot continue."%self)

        return installed

    def supportsPlatform(self,platform=None):
        """
        Check if a JPackage can be installed on a platform
        """
        if platform==None:
            relevant=j.system.platformtype.getMyRelevantPlatforms()
        else:
            relevant=j.system.platformtype.getParents(platform)
        for supportedPlatform in self.supportedPlatforms:
            if supportedPlatform in relevant:
                return True
        return False

    def _isHostPlatformSupported(self, platform):
        '''
        Checks if a given platform is supported, the checks takes the
        supported platform their parents in account.

        @param platform: platform to check
        @type platform: j.system.platformtype

        @return: flag that indicates if the given platform is supported
        @rtype: Boolean
        '''

        #@todo P1 no longer working use new j.system.platformtype

        supportedPlatformPool = list()

        for platform in self.supportedPlatforms:
            while platform != None:
                supportedPlatformPool.append(platform)
                platform = platform.parent

        if platform in supportedPlatformPool:
            return True
        else:
            return False

#############################################################################
#################################  ACTIONS  ################################
#############################################################################

    @JPLock
    def start(self,dependencies=False):
        """
        Start the JPackage, run the start tasklet(s)
        """
        # self.isInstalled(checkAndDie=True)
        
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.start(False)
        self.load()      
        self.actions.process_start()
        self.log('start')

    @JPLock
    def stop(self,dependencies=False,walkinstances=False):
        """
        Stop the JPackage, run the stop tasklet(s)
        """ 
        if self.name=="redis" and self.instance=="system":
            #this is required during bootstrap
            return
                      
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.stop(False)

        if walkinstances:
            for iname in self.getInstanceNames():
                self.load(iname)
                self.stop(walkinstances=False)
        else:
            if self.isInstalled():
                self.load()        
                self.actions.process_stop()
                self.log('stop')

    @JPLock
    def kill(self,dependencies=False):
        """
        Stop the JPackage, run the stop tasklet(s)
        """
        self.isInstalled(checkAndDie=True)
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.kill(False)
        self.load()        
        self.actions.process_kill()
        self.log('stop')

    @JPLock
    def monitor(self,dependencies=False,result=True):
        """
        Stop the JPackage, run the stop tasklet(s)
        """
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                result=result & dep.monitor(False,result)
        self.load()        
        print("monitor for: %s"%self)
        result=result&self.actions.monitor_up_local()
        return result

    @JPLock
    def monitor_net(self,ipaddr="localhost",dependencies=False,result=True):
        """
        Stop the JPackage, run the stop tasklet(s)
        """
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                result=result & dep.monitor(False,result)
        self.load()        
        result=result&self.actions.monitor_up_net(ipaddr=ipaddr)
        return result

    @JPLock
    def restart(self,dependencies=False):
        """
        Restart the JPackage
        """        
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.stop(False)
        self.load()
        self.actions.process_stop()
        self.actions.process_start()
        self.log('stop')


        # if dependencies:
        #     deps = self.getDependencies()
        #     for dep in deps:
        #         dep.restart(False)
        # self.loadActions()
        # self.stop()
        # self.start()

    def isrunning(self,dependencies=False,ipaddr="localhost"):
        """
        Check if application installed is running for jpackages
        """
        self.monitor(dependencies=dependencies)
        # self.monitor_up_net(dependencies=dependencies,ipaddr=ipaddr)
        self.log('isrunning')

    def reinstall(self, dependencies=False, download=True):
        """
        Reinstall the JPackage by running its install tasklet, best not to use dependancies reinstall 
        """                
        self.install(dependencies=dependencies, download=download, reinstall=True)

    @JPLock
    def prepare(self, dependencies=True, download=True):
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.install(False, download, reinstall=False)
        self.load()

        self.actions.install_prepare()

    @JPLock
    def copyfiles(self, dependencies=True, download=True):
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.copyfiles(dependencies=False, download=download)

        self.load()

        if self.debug ==True:
            self._copyfiles(doCodeRecipe=False)
            self.codeLink(dependencies=False, update=False, force=True)
        else:
            self.actions.install_copy()

    def installDebs(self):
        for platform in j.system.fs.listDirsInDir(self.getPathFiles(),dirNameOnly=True):
            if platform not in j.system.platformtype.getMyRelevantPlatforms():
                continue
            pathplatform=j.system.fs.joinPaths(self.getPathFiles(),platform)
            entries=j.system.fs.listDirsInDir(pathplatform,dirNameOnly=True)                    
            for ttype in entries:
                if ttype == 'debs':
                    fullpath = j.system.fs.joinPaths(pathplatform, ttype)
                    for file_ in sorted(j.system.fs.listFilesInDir(fullpath)):
                        j.system.platform.ubuntu.installDebFile(file_)

    def _copyfiles(self,doCodeRecipe=True):
        self._cleanupfiles(doCodeRecipe)
        for platform in j.system.fs.listDirsInDir(self.getPathFiles(),dirNameOnly=True):
            if platform not in j.system.platformtype.getMyRelevantPlatforms():
                continue
            
            #first do the debs otherwise the other dirs cannot overwrite what debs do
            self.installDebs()

            pathplatform=j.system.fs.joinPaths(self.getPathFiles(),platform)
            for ttype in j.system.fs.listDirsInDir(pathplatform,dirNameOnly=True):
                # print "type:%s,%s"%(ttype,ttype.find("cr_"))
                if doCodeRecipe==False and ttype.find("cr_")==0:
                    print("DO NOT COPY, because debug ")
                    continue #skip the coderecipe folders
                else:
                    pathttype=j.system.fs.joinPaths(pathplatform,ttype)
                    j.system.fs.removeIrrelevantFiles(pathttype)

                    if ttype in ["etc","cfg"]:
                        applyhrd=True
                    else:
                        applyhrd=False
                    if ttype == 'debs':
                        continue
                    tmp,destination=self.getBlobItemPaths(platform,ttype,"")
                    self.log("copy files from:%s to:%s"%(pathttype,destination))
                    self.__copyFiles(pathttype,destination,applyhrd=applyhrd)
        self._copyBlobInfo()

    def _cleanupfiles(self, doCodeRecipe):
        for platform, ttype in self.getBlobPlatformTypes(True):
            if not doCodeRecipe and ttype.startswith('cr_'):
                continue
            else:
                blobkey, keys = self.getBlobInfo(platform, ttype, active=True)
                for md5, relativefile in keys:
                    # print "1:'%s' '%s'"%(md5,relativefile)
                    blobpath, localpath = self.getBlobItemPaths(platform, ttype, relativefile)
                    # print "2:'%s' '%s'"%(blobpath,localpath)
                    if localpath != "/tmp":
                        j.system.fs.remove(localpath)

    def __copyFiles(self, path,destination,applyhrd=False):
        """
        Copy the files from package dirs to their proper location in the sandbox.

        @param destination: destination of the files
        """
        if destination=="":
            self._raiseError("A destination needs to be specified.") #done for safety, jpackage action scripts have to be adjusted

        print("pathplatform:%s"%path)
        #    self.log("Copy files from %s to %s"%(path,destination),category="copy")
        j.system.fs.createDir(destination,skipProtectedDirs=True)
        if applyhrd:
            tmpdir=j.system.fs.getTmpDirPath()
            j.system.fs.copyDirTree(path,tmpdir)
            j.application.config.applyOnDir(tmpdir)
            j.dirs.replaceFilesDirVars(tmpdir)
            j.system.fs.copyDirTree(tmpdir, destination,skipProtectedDirs=True)
            j.system.fs.removeDirTree(tmpdir)
        else:
            j.system.fs.copyDirTree(path, destination,keepsymlinks=True,skipProtectedDirs=True)

    @JPLock
    def install(self, dependencies=True, download=True, reinstall=False,reinstalldeps=False,update=False,instance=None,hrddata={}):
        """
        Install the JPackage

        @param dependencies: if True, all dependencies will be installed too
        @param download:     if True, bundles of package will be downloaded too
        @param reinstall:    if True, package will be reinstalled

        when dependencies the reinstall will not be asked for there

        """
        if not self.supportsPlatform():
            self._raiseError("Only those platforms are supported by this package %s your system supports the following platforms: %s" % (str(self.supportedPlatforms), str(j.system.platformtype.getMyRelevantPlatforms())))

        key="%s_%s"%(self.domain,self.name)
        if key in j.packages.inInstall:
            print("are already in install of jpackage")
            return

        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                print("**%s asks for dependency:%s"%(self,dep))
                dep.install(False, download, reinstall=reinstalldeps,hrddata=hrddata)

        # If I am already installed assume my dependencies are also installed
        if self.buildNr != -1 and self.buildNr <= self.state.lastinstalledbuildnr and not reinstall and self.isInstalled(instance):
            self.log('already installed')            
            # if str(instance) in self.getInstanceNames():
            #     self.configure(dependencies=dependencies,instance=instance,hrddata=hrddata)
            return # Nothing to do

        j.packages.inInstall.append(key)
        if instance is None:
            instance = 0

        self.instance=instance

        self._copyMetadataToActive(hrddata=hrddata)
        
        self.load(force=True,instance=instance) #reload actions to make sure new hrdactive are applied

        self.stop()

        if download:
            self.download(dependencies=False)

        if reinstall or self.buildNr > self.state.lastinstalledbuildnr:
            #print 'really installing ' + str(self)
            self.log('installing')
            if self.state.checkNoCurrentAction == False:
                self._raiseError("jpackages is in inconsistent state, ...")
            
            self.prepare(dependencies=False)            

            self.copyfiles(dependencies=False)

            self.actions.install_post()

            if self.buildNr==-1:
                self.buildNr=0

        if self.debug:
            self.log('install for debug (link)')
            self.codeLink(dependencies=False, update=False, force=True)

        if not update:
            # if self.buildNr==-1 or self.configchanged or reinstall or self.buildNr > self.state.lastinstalledbuildnr:
            self.configure(dependencies=False)

        if self.buildNr<0:
            self.buildNr=0
        self.state.setLastInstalledBuildNr(self.buildNr)

        j.packages.inInstall.remove(key)

    def isNew(self):
        if self.buildNr==-1 or self.buildNr > self.state.lastinstalledbuildnr:
            return True
        return False

    @JPLock
    def uninstall(self, unInstallDependingFirst=False):
        """
        Remove the JPackage from the sandbox. In case dependent JPackages are installed, the JPackage is not removed.

        @param unInstallDependingFirst: remove first dependent JPackages
        """
        # Make sure there are no longer installed packages that depend on me
        ##self.assertAccessable()
        
        self.loadActions()
        if unInstallDependingFirst:
            for p in self.getDependingInstalledPackages(errorIfNotFound=False):
                p.uninstall(True)
        if self.getDependingInstalledPackages(recursive=True,errorIfNotFound=False):
            self._raiseError('Other package on the system dependend on this one, uninstall them first!')
        j.tools.startupmanager.remove4JPackage(self)
        tag = "install"
        action = "uninstall"
        state = self.state
        if state.checkNoCurrentAction == False:
            self._raiseError("jpackages is in inconsistent state, ...")
        self.log('uninstalling' + str(self))
        self.actions.uninstall()
        state.setLastInstalledBuildNr(-1)

    def prepareForUpdatingFiles(self, suppressErrors=False):
        """
        After this command the operator can change the files of the jpackages.
        Files do not aways come from code repo, they can also come from jpackages repo only
        """
        j.system.fs.createDir(self.getPathFiles())
        if  self.state.prepared != 1:
            if not self.isNew():
                self.download(suppressErrors=suppressErrors)
                self._expand(suppressErrors=suppressErrors)
            self.state.setPrepared(1)

    @JPLock
    def configure(self, dependencies=False,instance=None,hrddata={}):
        """
        Configure the JPackage after installation, via the configure tasklet(s)
        """
        self.log('configure')
        
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.configure(dependencies=False)

        if instance==None and self.instance is None:
            for instanceName in self.getInstanceNames():
                self.instance=instanceName
                self.configure(dependencies=False,instance=instanceName)
            return

        self._copyMetadataToActive(hrddata=hrddata)

        self.load(force=True)

        self.actions.install_configure()
        
        self.actions.process_configure()
        # self.state.setIsPendingReconfiguration(False)
        j.application.loadConfig() #makes sure hrd gets reloaded to application.config object

    @JPLock
    def codeExport(self, dependencies=False, update=None):
        """
        Export code to right locations in sandbox or on system
        code recipe is being used
        only the sections in the recipe which are relevant to you will be used
        """        
        self.load()
        self.log('CodeExport')
        if dependencies == None:
            j.gui.dialog.askYesNo(" Do you want to link the dependencies?", False)
        if update == None:
            j.gui.dialog.askYesNo(" Do you want to update your code before exporting?", True)
        if update:
            self.codeUpdate(dependencies)
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.codeExport(dependencies=False,update=update)

    @JPLock
    def codeUpdate(self, dependencies=False, force=False):
        """
        Update code from code repo (get newest code)
        """
        self.log('CodeUpdate')
        self.load(findDefaultInstance=False)
        # j.clients.mercurial.statusClearAll()
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.codeUpdate(dependencies=False,force=force)
        self.actions.code_update()

    @JPLock
    def codeCommit(self, dependencies=False, push=False):
        """
        update code from code repo (get newest code)
        """
        
        self.load(findDefaultInstance=False)
        self.log('CodeCommit')
        j.clients.mercurial.statusClearAll()
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.codeCommit(dependencies=False,push=push)
        self.actions.code_commit()
        if push:
            self.codePush(dependencies)

    # @JPLock
    # def codePush(self, dependencies=False, merge=True):
    #     """
    #     Push code to repo (be careful this can brake code of other people)
    #     """        
    #     self.load()
    #     j.log("CodePush")
    #     j.clients.mercurial.statusClearAll()
    #     if dependencies:
    #         deps = self.getDependencies()
    #         for dep in deps:
    #             dep.codePush(merge=merge)
    #     self.actions.code_push(merge=merge)

    @JPLock
    def codeLink(self, dependencies=False, update=False, force=True):
        """
        Link code from local repo to right locations in sandbox

        @param force: if True, do an update which removes the changes (when using as install method should be True)
        """
        self.load() 

        # j.clients.mercurial.statusClearAll()
        self.log("CodeLink")
        if dependencies is None:
            if j.application.shellconfig.interactive:
                dependencies = j.gui.dialog.askYesNo("Do you want to link the dependencies?", False)
            else:
                self._raiseError("Need to specify arg 'depencies' (true or false) when non interactive")


        if update is None:
            if j.application.shellconfig.interactive:
                update = j.gui.dialog.askYesNo("Do you want to update your code before linking?", True)
            else:
                self._raiseError("Need to specify arg 'update' (true or false) when non interactive")

        if update:
            self.codeUpdate(dependencies, force=force)

        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.codeLink(dependencies=False, update=update,force=force)            

        hrdpath=j.system.fs.joinPaths(self.getPathMetadata(),"hrd","code.hrd")
        codehrd=j.core.hrd.getHRD(hrdpath)
        account=codehrd.getStr("jp.code.account")
        repo=codehrd.getStr("jp.code.repo")
        if account=="" or repo=="":
            return

        self.actions.code_link(force=force)
      
    @JPLock
    def package(self, dependencies=False,update=False):
        """
        copy files from code recipe's and also manually copied files in the files sections

        @param dependencies: whether or not to package the dependencies
        @type dependencies: boolean
        """
        
        self.load(instance=None,findDefaultInstance=False)

        self.log('Package')
        # Disable action caching:
        # If a user packages for 2 different platforms in the same jshell
        # instance, the second call is just ignored, which is not desired
        # behaviour.
        # Also, when a user packages once, then sees a need to update his/her
        # code, and then packages again in the same jshell, again the second
        # time would be a non-op, which is again not desired. So we disable the
        # action caching for this action.
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.package()
        if update:
            self.actions.code_update()

        self.actions.code_package()

        newbuildNr = False

        newblobinfo = self._calculateBlobInfo()

        actionsdir=j.system.fs.joinPaths(self.getPathMetadata(), "actions")
        j.system.fs.removeIrrelevantFiles(actionsdir)
        taskletsChecksum, descr2 = j.tools.hash.hashDir(actionsdir)
        hrddir=j.system.fs.joinPaths(self.getPathMetadata(), "hrdactive")
        hrdChecksum, descr2 = j.tools.hash.hashDir(hrddir)
        descrdir=j.system.fs.joinPaths(self.getPathMetadata(), "documentation")
        descrChecksum, descr2 = j.tools.hash.hashDir(descrdir)

        if descrChecksum != self.descrChecksum:
            self.log("Descr change.",level=5,category="buildNr")
            #buildNr needs to go up
            newbuildNr = True
            self.descrChecksum = descrChecksum
        else:
            self.log("Descr did not change.",level=7,category="buildNr")

        if taskletsChecksum != self.taskletsChecksum:
            self.log("Actions change.",level=5,category="buildNr")
            #buildNr needs to go up
            newbuildNr = True
            self.taskletsChecksum = taskletsChecksum
        else:
            self.log("Actions did not change.",level=7,category="buildNr")            

        if hrdChecksum != self.hrdChecksum:
            self.log("Active HRD change.",level=5,category="buildNr")
            #buildNr needs to go up
            newbuildNr = True
            self.hrdChecksum = hrdChecksum
        else:
            self.log("Active HRD did not change.",level=7,category="buildNr")        

        if newbuildNr or newblobinfo:
            if newbuildNr:
                self.buildNrIncrement()
            self.log("new buildNr is:%s"%self.buildNr)
            self.save()
            self.load()

    def _calculateBlobInfo(self):
        result = False
        filesdir = j.system.fs.joinPaths(self.getPathMetadata(),"files")

        pathfiles = self.getPathFiles()
        if not j.system.fs.exists(pathfiles):
            return result

        for platform in j.system.fs.listDirsInDir(pathfiles,dirNameOnly=True):
            pathplatform=j.system.fs.joinPaths(self.getPathFiles(),platform)
            for ttype in j.system.fs.listDirsInDir(pathplatform,dirNameOnly=True):
                pathttype=j.system.fs.joinPaths(pathplatform,ttype)
                j.system.fs.removeIrrelevantFiles(pathttype,followSymlinks=False)
                md5,llist=j.tools.hash.hashDir(pathttype)
                if llist=="":
                    continue
                out="%s\n"%md5
                out+=llist

                oldkey,olditems=self.getBlobInfo(platform,ttype)
                if oldkey != md5:
                    if not result:
                        self.buildNrIncrement()
                    result = True

                    dest=j.system.fs.joinPaths(self.getPathMetadata(),"files","%s___%s.info"%(platform,ttype))
                    j.system.fs.createDir(j.system.fs.getDirName(dest))
                    j.system.fs.writeFile(dest,out)

                    dest=j.system.fs.joinPaths(self.getPathMetadata(),"uploadhistory","%s___%s.info"%(platform,ttype))
                    out="%s | %s | %s | %s\n"%(j.base.time.getLocalTimeHR(),j.base.time.getTimeEpoch(),self.buildNr,md5)
                    j.system.fs.writeFile(dest, out, append=True)
                    self.log("Uploaded changed for platform:%s type:%s"%(platform,ttype),level=5,category="upload" )
                else:
                    self.log("No file change for platform:%s type:%s"%(platform,ttype),level=5,category="upload" )
        return result

    @JPLock
    def compile(self,dependencies=False):
        
        self.load()
        params = j.core.params.get()
        params.jpackages = self
        self.log('Compile')
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.compile()
        self.actions.compile()

    @JPLock
    def download(self, dependencies=False, destination=None, suppressErrors=False, allplatforms=False,force=False,expand=True,nocode=False,instance=None):
        """
        Download the jpackages & expand
        """        
        self.load(instance=instance,findDefaultInstance=False)
        if self.debug:
            nocode=True

        if dependencies==None and j.application.shellconfig.interactive:
            dependencies = j.console.askYesNo("Do you want all depending packages to be downloaded too?")
        else:
            dependencies=dependencies
        
        if instance != None:
            self.instance=instance
        

        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.download(dependencies=False, destination=destination,allplatforms=allplatforms,expand=expand,nocode=nocode)

        self.actions.install_download(expand=expand,nocode=nocode)

    def _download(self,destination=None,force=False,expand=True,nocode=False):
        
        j.packages.getDomainObject(self.domain)

        self.log('Downloading.')

        for platform,ttype in self.getBlobPlatformTypes():
            
            if ttype[0:3]=="cr_":
                if nocode:
                    print("no need to download (option nocode):%s %s"%(self,ttype))
                    continue
                
            if destination==None:
                downloaddestination=j.system.fs.joinPaths(self.getPathFiles(),platform,ttype)
            else:
                downloaddestination = destination

            
            checksum,files=self.getBlobInfo(platform,ttype)

            self.log("key found:%s for platform:%s type:%s"%(checksum,platform,ttype),category="download",level=6)
            
            key="%s_%s"%(platform,ttype)
            
            if not self.blobstorLocal.exists(checksum):
                print("try to find remote")
                self.blobstorRemote.copyToOtherBlobStor(checksum, self.blobstorLocal)

            force=True

            if force==False and key in self.state.downloadedBlobStorKeys and self.state.downloadedBlobStorKeys[key] == checksum:
                self.log("No need to download/expand for platform_type:'%s', already there."%key,level=5)
                continue

            self.log("expand platform_type:%s"%key,category="download")
            j.system.fs.removeDirTree(downloaddestination)
            j.system.fs.createDir(downloaddestination)
            self.blobstorLocal.download(checksum, downloaddestination)
            self.state.downloadedBlobStorKeys[key] = checksum
            self.state.save()

        return True

    @JPLock
    def backup(self,url=None,dependencies=False):
        """
        Make a backup for this package by running its backup tasklet.
        """
        
        if url==None:
            url = j.console.askString("Url to backup to?")
        else:
            self._raiseError("url needs to be specified")

        self.load()
        params = j.core.params.get()
        params.jpackages = self
        params.url=url
        self.log('Backup')
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.backup(url=url)
        self.actions.backup()

    @JPLock
    def restore(self,url=None,dependencies=False):
        """
        Make a restore for this package by running its restore tasklet.
        """
        
        if url==None:
            url = j.console.askString("Url to restore to?")
        else:
            self._raiseError("url needs to be specified")
        self.log('restore')
        self.load()
        params = j.core.params.get()
        params.jpackages = self
        params.url=url
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.restore(url=url)
        self.actions.restore()        

    def upload(self, remote=True, local=True,dependencies=False,onlycode=False):

        if dependencies==None and j.application.shellconfig.interactive:
            dependencies = j.console.askYesNo("Do you want all depending packages to be downloaded too?")
        else:
            dependencies=dependencies

        self.load(instance=None,findDefaultInstance=False)
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.upload(remote=remote, local=local,dependencies=False,onlycode=onlycode)

        self.actions.upload(onlycode=onlycode)

    def getBlobKeysActive(self):
        keys=[]
        for platform,ttype in self.getBlobPlatformTypes():
            key0,blobitems=self.getBlobInfo(platform,ttype)
            keys.append(key0)
        return keys

    def uploadExistingBlobs(self,blobserver,dependencies=False):
        """
        @return the non found keys
        """
        self.loadBlobStores()
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.uploadExistingBlobs(blobserver=blobserver)

        keys=self.getBlobKeysActive()
        bservernew=j.clients.blobstor.get(blobserver)
        notfound=[]
        for key in keys:
            print(self, end=' ')
            if not bservernew.exists(key):
                #does not exist on remote bserver yet
                print("blob %s not on dest."%(key), end=' ')
                if self.blobstorLocal.exists(key):
                    print("upload from local.")
                    self.blobstorLocal.copyToOtherBlobStor(key, bservernew)
                elif self.blobstorRemote.exists(key):
                    print("upload from remote.")
                    
                    self.blobstorRemote.copyToOtherBlobStor(key, bservernew)
                else:
                    print("blob %s not on sources."%key)
                    notfound.append(key)
        return notfound

    def uploadExistingBlobsFromHistory(self,blobserver="jpackages_remote"):
        """
        @return the non found keys
        """
        self.loadBlobStores()
        bservernew=j.clients.blobstor.get(blobserver)
        hist=self.getBlobHistory()
        for ttype in list(hist.keys()):
            epochs=list(hist[ttype].keys())#[int(item) for item in hist[ttype].keys()]
            epochs.sort()
            epochs.reverse()
            for epoch in epochs:
                key=hist[ttype][epoch][1]
                print("%s %s %s %s"%(self.domain,self.name,ttype,hist[ttype][epoch][0]))
                if bservernew.exists(key):
                    print("found")
                    break
                else:
                    #does not exist on remote bserver yet
                    print("blob %s not on dest."%(key), end=' ')
                    if self.blobstorLocal.exists(key):
                        print("upload from local.")
                        self.blobstorLocal.copyToOtherBlobStor(key, bservernew)
                        break
                    elif self.blobstorRemote.exists(key):
                        print("upload from remote.")
                        self.blobstorRemote.copyToOtherBlobStor(key, bservernew)
                        break

    def checkExistingBlobs(self,blobserver,dependencies=False):
        """
        @return the non found keys
        """
        self.loadBlobStores()
        if dependencies:
            deps = self.getDependencies()
            for dep in deps:
                dep.uploadExistingBlobs(blobserver=blobserver)

        keys=self.getBlobKeysActive()
        bservernew=j.clients.blobstor.get(blobserver)
        notfound=[]
        for key in keys:
            print(self, end=' ')
            if not bservernew.exists(key):
                notfound.append(key)
        return notfound

    def getBlobHistory(self):
        blobtypes=self.getBlobPlatformTypes()
        result={}
        for btype in blobtypes:            
            btype2="___".join(btype)
            result[btype2]={}
            path="%s/uploadhistory/%s.info"%(self.getPathMetadata(),btype2)
            if not j.system.fs.exists(path):
                print("ERROR: COULD NOT FIND %s"%path)
            else:
                C=j.system.fs.fileGetContents(path)
                for line in C.split("\n"):
                    if line.strip() != "":

                        hrtime,ttime,nr,md5= line.split("|")
                        md5=md5.strip()
                        result[btype2][ttime]=(hrtime,md5)
        return result        



    @JPLock
    def _upload(self, remote=True, local=True,onlycode=False):
        """
        Upload jpackages to Blobstor, default remote and local
        """

        self.load(instance=None,findDefaultInstance=False)

        self._calculateBlobInfo()
        
        for platform,ttype in self.getBlobPlatformTypes():

            key0,blobitems=self.getBlobInfo(platform,ttype)

            pathttype=j.system.fs.joinPaths(self.getPathFiles(),platform,ttype)

            if ttype[0:3] != "cr_" and onlycode:
                print("no need to upload (onlycode option):%s %s %s"%(self,platform,ttype))
                continue

            if not j.system.fs.exists(pathttype):

                self._raiseError("Could not find files section:%s, check the files directory in your jpackages metadata dir, maybe there is a .info file which is wrong & does not exist here."%pathttype)

            self.log("Upload platform:'%s', type:'%s' files:'%s'"%(platform,ttype,pathttype),category="upload")
        
            if local and remote and self.blobstorRemote != None and self.blobstorLocal != None:
                key, descr,uploadedAnything = self.blobstorLocal.put(pathttype)
                self.blobstorLocal.copyToOtherBlobStor(key,self.blobstorRemote)
                # key, descr,uploadedAnything  = self.blobstorRemote.put(pathttype)
            elif local and self.blobstorLocal != None:
                key, descr, uploadedAnything = self.blobstorLocal.put(pathttype, blobstors=[])
            elif remote and self.blobstorRemote != None:
                key, descr, uploadedAnything = self.blobstorRemote.put(pathttype, blobstors=[])
            else:
                self._raiseError("need to upload to local or remote")


            # if uploadedAnything:
            #     self.log("Uploaded blob for %s:%s:%s to blobstor."%(self,platform,ttype))
            # else:
            #     self.log("Blob for %s:%s:%s was already on blobstor, no need to upload."%(self,platform,ttype))

            if key0 != key:
                self._raiseError("Corruption in upload for %s"%self)

    @JPLock
    def waitUp(self, timeout=60,dependencies=False):        
        self.load()
        if dependencies:
            deps = self.getDependencies()
        else:
            deps=[]

        start=j.base.time.getTimeEpoch()
        now=start
        while now<start+timeout:
            result=True
            for dep in deps:
                # result=result & dep.actions.monitor_up_net()
                result &= dep.actions.monitor_up_local()
            # result=result & self.actions.monitor_up_net()
            result &= self.actions.monitor_up_local()
            if result:
                return True
            time.sleep(0.5)
            print("waitup:%s"%self)
            now=j.base.time.getTimeEpoch()
        self._raiseErrorOps("Timeout on waitup for jp:%s"%self)

    @JPLock
    def waitDown(self, timeout=60,dependencies=False):  
        self.log("waitdown: not implemented")
        return True

        self.load()
        if dependencies:
            deps = self.getDependencies()
        else:
            deps=[]

        start=j.base.time.getTimeEpoch()
        now=start
        while now<start+timeout:
            result=True
            for dep in deps:
                result &= not(dep.actions.monitor_up_net())
            result &= not(self.actions.monitor_up_net())

            if result:
                return True

            time.sleep(0.5)
            print("waitdown:%s"%self)
            now=j.base.time.getTimeEpoch()

        self._raiseErrorOps("Timeout on waitdown for jp:%s"%self)


    @JPLock
    def processDepCheck(self, timeout=60,dependencies=False):
        #check for dependencies for process to start
        self.load()
        if dependencies:
            deps = self.getDependencies()
        else:
            deps=[]            
            
        start=j.base.time.getTimeEpoch()
        now=start

        while now<start+timeout:
            result=True
            for dep in deps:
                r=dep.actions.process_depcheck()
                if r == False:
                    result = False
            r=self.actions.process_depcheck()
            if r == False:
                result = False
            if result != False:
                return True
            time.sleep(0.5)
            print("processdepcheck:%s"%self)
            now=j.base.time.getTimeEpoch()
        self._raiseErrorOps("Timeout on check process dependencies for jp:%s"%self)


########################################################################
#########################  RECONFIGURE  ################################
########################################################################

    def signalConfigurationNeeded(self):
        """
        Set in the corresponding jpackages's state file if reconfiguration is needed
        """
        self.state.setIsPendingReconfiguration(True)
        j.packages._setHasPackagesPendingConfiguration(True)

    def isPendingReconfiguration(self):
        """
        Check if the JPackage needs reconfiguration
        """
        if self.state.getIsPendingReconfiguration() == 1:
            return True
        return False


#########################################################################
####################### SHOW ############################################

    def showDependencies(self):
        """
        Return all dependencies of the JPackage.
        See also: addDependency and removeDependency
        """        
        self._printList(self.getDependencies())
            
    def showDependingInstalledPackages(self):
        """
        Show which jpackages have this jpackages as dependency.
        Do this only for the installed jpackages.
        """
        self._printList(self.getDependingInstalledPackages())

    def showDependingPackages(self):
        """
        Show which jpackages have this jpackages as dependency.
        """
        self._printList(self.getDependingPackages())

    def _printList(self, arr):
        for item in arr:
            j.console.echo(item)        

#########################################################################
#######################  SUPPORTING FUNCTIONS  ##########################

    def _getDomainObject(self):
        """
        Get the domain object for this Q-Package

        @return: domain object for this Q-Package
        @rtype: Domain.Domain
        """
        return j.packages.getDomainObject(self.domain)

    def _raiseError(self,message,category="jpackage"):
        ##self.assertAccessable()
        message = "INPUTERROR: %s for jpackage %s_%s_%s (%s)" % (message, self.domain, self.name, self.version,self.instance)
        j.events.inputerror_critical(message,category) 

    def _raiseErrorOps(self,message,category="jpackage"):
        ##self.assertAccessable()
        message = "OPSERROR: %s for jpackage %s_%s_%s (%s)" % (message, self.domain, self.name, self.version,self.instance)
        j.events.opserror_critical(message,category) 

    def _clear(self):
        ##self.assertAccessable()
        """
        Clear all properties except domain, name, and version
        """
        self.tags = []
        self.supportedPlatforms=[]
        self.buildNr = 0
        self.dependencies = []
        self.dependenciesNames = {}


    def __cmp__(self,other):
        if other == None or other=="":
            return False
        return self.name == other.name and str(self.domain) == str(other.domain) and j.packages._getVersionAsInt(self.version) == j.packages._getVersionAsInt(other.version)

    def __repr__(self):
        return self.__str__()

    def _resetPreparedForUpdatingFiles(self):
        self.state.setPrepared(0)

    def __str__(self):
        return "JPackage %s %s %s (%s) " % (self.domain, self.name, self.version,self.instance)

    def __eq__(self, other):
        return str(self) == str(other)

    def reportNumbers(self):
        return ' buildNr:' + str(self.buildNr)
