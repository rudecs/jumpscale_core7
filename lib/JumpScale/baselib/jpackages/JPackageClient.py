import math
from JumpScale import j
from .JPackageObject import JPackageObject
import copy

class JPackageClient():
    sourcesFile = None

    """
    methods to deal with jpackages, seen from client level

    @qlocation j.packages
    """
    def __init__(self):
        """
        
        """
        self.__init=False
        self.redis=j.application.redis

    def __getChildObjectsExamples(self):
        res={}
        res["j.packages._object.jpackage"]=self.findByName("core")
        return res        

    def _init(self):
        if self.__init:
            return
        from .Domain import Domain
        self.__init=True

        # try:
        #     import JumpScale.baselib.expect
        # except:
        #     pass
            
        from JumpScale.baselib import platforms

        import JumpScale.baselib.actions
        import JumpScale.baselib.taskletengine
        import JumpScale.baselib.blobstor
        import JumpScale.baselib.cloudsystemfs            

        # if j.application.config.exists("jumpscale.paths.jpackages.files"):
        #     self.packageDirFiles=j.application.config.get("jumpscale.paths.jpackages.files")
        # else:
        self.packageDirFiles=j.system.fs.joinPaths(j.dirs.packageDir, "files")

        # if hasattr("j","basepath"):
        #     self.packageDirFiles=self.packageDirFiles.replace("$base",j.basepath)

        if j.application.sandbox:
            j.dirs.packageDirMD=j.system.fs.joinPaths(j.dirs.baseDir,"jpackages")
        else:
            j.dirs.packageDirMD=j.system.fs.joinPaths(j.dirs.varDir, "jpackages","metadata")

        j.system.fs.createDir(j.dirs.packageDirMD)

        self.domains=[]

        self._metadatadirTmp=j.system.fs.joinPaths(j.dirs.varDir,"tmp","jpackages","md")

        j.system.fs.createDir(self._metadatadirTmp)        
        # can't ask username here
        # because jumpscale is not interactive yet
        # So we ask the username/passwd lazy in the domain object
        # j.packages.markConfigurationPending=self._runPendingReconfigeFiles
        self.reloadconfig()
        self.enableConsoleLogging()

        self.logenable=True
        self.loglevel=5
        self.errors=[]
        self.inInstall=[] #jpackages which are being installed

    def reportError(self,msg):
        self.errors.append(msg)

    def log(self,msg,category="",level=5):
        if not hasattr(self, 'loglevel'):
            self.loglevel = 5
        if not hasattr(self, 'logenable'):
            self.logenable = True
        if level<self.loglevel+1 and self.logenable:
            j.logger.log(msg,category="jpackage.%s"%category,level=level)        


    def enableConsoleLogging(self):
        j.logger.consoleloglevel=6
        j.logger.consolelogCategories.append("jpackage")
        j.logger.consolelogCategories.append("blobstor")

    def getJPackageMetadataScanner(self):
        """
        returns tool which can be  used to scan the jpackages repo's and manipulate them
        """
        self._init()
        
        from core.jpackages.JPackageMetadataScanner import JPackageMetadataScanner
        return JPackageMetadataScanner()

    def _renew(self):
        j.packages = JPackageClient()

    def checkProtectedDirs(self,redo=True,checkInteractive=True):
        """
        recreate the config file for protected dirs (means directories linked to code repo's)
        by executing this command you are sure that no development data will be overwritten
        @param redo means, restart from existing links in qbase, do not use the config file
        @checkInteractive if False, will not ask just execute on it
        """
        raise RuntimeError("reimplement")
        result,llist=j.system.process.execute("find /opt/qbase5 -type l")
        lines=[item for item in llist.split("\n") if item.strip() != ""]
        if len(lines)>0:
            cfgpath=j.system.fs.joinPaths(j.dirs.cfgDir,"debug","protecteddirs","protected.cfg")
            if redo==False and j.system.fs.exists(cfgpath):
                llist=j.system.fs.fileGetContents(cfgpath)
                lines.extend([item for item in llist.split("\n") if item.strip() != ""])
            prev=""
            lines2=[]
            lines.sort()
            for line in lines:
                if line != prev:
                    lines2.append(line)
                prev=line
            out="\n".join(lines2)
            do=False
            if checkInteractive: 
                if j.console.askYesNo("Do you want to make sure that existing linked dirs are not overwritten by installer? \n(if yes the linked dirs will be put in protected dir configuration)\n"):
                    do=True
            else:
                do=True
            if do:
                j.system.fs.writeFile(cfgpath,out)     

    def reloadconfig(self):
        """
        Reload all jpackages config data from disk
        """
        if not self.__init:
            self._init()

        from .Domain import Domain
        cfgpath=j.system.fs.joinPaths(j.dirs.cfgDir, 'jpackages', 'sources.cfg')

        if not j.system.fs.exists(cfgpath):
            j.system.fs.createDir(j.system.fs.getDirName(cfgpath))
            raise RuntimeError("did not find jpackage sources file on %s"%cfgpath)            
        else:
            cfg = j.tools.inifile.open(cfgpath)
            self.sourcesConfig=cfg
            domainDict = dict()
            for domains in self.domains: 
                domainDict[domains.domainname] = domains
            for domain in cfg.getSections():
                if domain in list(domainDict.keys()):
                    self.domains.remove(domainDict[domain])
                self.domains.append(Domain(domainname=domain))

    def create(self, domain="", name="", version="1.0", description="", supportedPlatforms=None):
        """
        Creates a new jpackages4, this includes all standard tasklets, a config file and a description.wiki file
        @param domain:      string - The domain the new jpackages should reside in
        @param name:        string - The name of the new jpackages
        @param version:     string - The version of the new jpackages
        @param description: string - The description of the new jpackages (is stored in the description.wiki file)
        @param supportedPlatforms  ["linux",...] other examples win,win32,linux64 see j.system.platformtype
        """
        self._init()    
        if j.application.shellconfig.interactive:
            if not domain:
                domain  = j.console.askChoice(j.packages.getDomainNames(), "Please select a domain")
            j.packages.getDomainObject(domain)._ensureDomainCanBeUpdated() #@question what does this do?

            if not name:
                name    = j.console.askString("Please provide a name")
            if not version:
                version = j.console.askString("Please provide a version","1.0")
            if not description:
                description = j.console.askString("Please provide a description","")

            while not supportedPlatforms:
                supportedPlatforms = j.console.askChoiceMultiple(sorted(j.system.platformtype.getPlatforms()), 'Please enumerate the supported platforms')

        if domain=="" or name=="":
            raise RuntimeError("domain or name at least needs to be specified")

        supportedPlatforms=[str(item) for item in supportedPlatforms]
        # Create one in the repo
        if not domain in j.packages.getDomainNames():
            raise RuntimeError('Provided domain is nonexistent on this system')
        if self.getDomainObject(domain).metadataFromTgz:
            raise RuntimeError('The meta data for domain ' + domain + ' is coming from a tgz, you cannot create new packages in it.')
        jp      = JPackageObject(domain, name, version)
        #jp.prepareForUpdatingFiles(suppressErrors=True)
        jp.supportedPlatforms = supportedPlatforms
        jp.description=description
        jp.save()
        j.system.fs.createDir(jp.getPathFiles())
        j.system.fs.createDir(j.system.fs.joinPaths(jp.getPathFiles(),"generic"))
        for pl in supportedPlatforms:
            j.system.fs.createDir(j.system.fs.joinPaths(jp.getPathFiles(),"%s"%pl))

        return jp


############################################################
##################  GET FUNCTIONS  #########################
############################################################

    def getTypePath(self, ttype, relativepath,jp=None):
        if ttype in ('sitepackages', 'site-packages'):
            if j.application.sandbox:
                base=j.system.fs.joinPaths(j.dirs.baseDir,"libext")
            else:
                base=j.application.config.get("python.paths.local.sitepackages")
            systemdest = j.system.fs.joinPaths(base, relativepath)
        elif ttype=="root":
            systemdest = "/%s"%relativepath.lstrip("/")
        elif ttype=="base":
            systemdest = j.system.fs.joinPaths(j.dirs.baseDir, relativepath)
        elif ttype=="app":
            if jp==None:
                raise RuntimeError("getTypePath doesnt have access to jp object, jp==None")
            # if jp.hrd_instance==None:                
            #     raise RuntimeError("Cannot link jpackage, did not find instance version.") 
            if jp.hrd_instance != None:
                path = jp.getAppPath()
                systemdest = j.system.fs.joinPaths(path, relativepath)
            else:
                systemdest=None
        elif ttype=="apps":
            systemdest = j.system.fs.joinPaths(j.dirs.baseDir,"apps",relativepath)
        elif ttype=="cfg":
            systemdest = j.system.fs.joinPaths(j.dirs.cfgDir, relativepath)
        elif ttype=="code":
            systemdest = j.system.fs.joinPaths(j.dirs.codeDir, relativepath)
        elif ttype=="var":
            systemdest = j.system.fs.joinPaths(j.dirs.varDir, relativepath)
        elif ttype=="jslib":
            systemdest = j.system.fs.joinPaths(j.dirs.jsLibDir, relativepath)
        elif ttype=="lib":
            systemdest = j.system.fs.joinPaths(j.dirs.libDir, relativepath)
        elif ttype=="libext":
            systemdest = j.system.fs.joinPaths(j.dirs.libExtDir, relativepath)
        elif ttype=="jsbin":
            systemdest = j.system.fs.joinPaths(j.dirs.binDir, relativepath)
        elif ttype=="opt":
            base="/opt"
            systemdest = j.system.fs.joinPaths(base, relativepath)
        elif ttype=="debs":
            systemdest = "/tmp"
        elif ttype=="etc":
            base="/etc"
            systemdest = j.system.fs.joinPaths(base, relativepath)
        elif ttype=="tmp":
            systemdest = j.system.fs.joinPaths(j.dirs.tmpDir, relativepath)
        elif ttype=="bin":            
            base=j.application.config.get("bin.local")
            if base.strip()=="":
                base="/usr/local/bin/"
            systemdest = j.system.fs.joinPaths(base, relativepath)
        else:
            base=j.application.config.applyOnContent(ttype)
            if base==ttype:
                raise RuntimeError("Could not find ttype:%s for %s, needs to be root,base,etc,bin,debs"%(ttype,self))
            systemdest = j.system.fs.joinPaths(base, relativepath)
        return systemdest

    def getActionNamesClass(self):
        """
        these actions can be applied on jpackage without knowing the jpackage instance
        """
        res=["code.commit","code.package","code.push","code.update","process.depcheck","upload", "install.download"]
        return res

    def getActionNamesInstance(self):
        res=["code.export","code.link","data.export","data.import","data.logrotate","install.configure","install.copy","install.download",\
            "install.post","install.prepare","monitor.getstats","monitor.up.local","monitor.up.net",\
            "process.configure","process.kill","process.start","process.stop","process.unconfigure","uninstall"]
        return res

    def get(self, domain, name, version,instance=0):
        """
        Returns a jpackages 
        @param domain:  string - The domain the jpackages is part from
        @param name:    string - The name of the jpackages
        @param version: string - The version of the jpackages
        """
        if domain.find("jp_")==0:
            raise RuntimeError("domain should not start with jp_")
        self._init()
        # return a package from the default repo
        key = '%s%s%s' % (domain,name,version)
        if key in self._getcache:
            return self._getcache[key]
        if self.exists(domain,name,version)==False:
            raise RuntimeError("Could not find package %s." % self.getMetadataPath(domain,name,version))
        self._getcache[key]=JPackageObject(domain, name, version,instance=instance)
        return self._getcache[key]

                    
    def exists(self,domain,name,version):
        """
        Checks whether the jpackages's metadata path is currently present on your system
        """
        self._init()
        return j.system.fs.exists(self.getMetadataPath(domain,name,version))

    def getInstalledPackages(self):
        """
        Returns a list of all currently installed packages on your system
        """
        self._init()
        return [p for p in self.getJPackageObjects(j.system.platformtype.myplatform) if p.isInstalled()]

    def getDebugPackages(self):
        """
        Returns a list of all currently installed packages on your system
        """
        self._init()
        return [p for p in self.getJPackageObjects(j.system.platformtype.myplatform) if int(p.state.debugMode)==1]

    def getPackagesWithBrokenDependencies(self):
        """
        Returns a list of all jpackages which have dependencies that cannot be resolved
        """
        self._init()
        return [package for package in self.getJPackageObjects() if len(package.getBrokenDependencies()) > 0]
    
    def getPendingReconfigurationPackages(self):
        """
        Returns a List of all jpackages that are pending for configuration
        """
        self._init()
        return [jpackages for jpackages in self.getJPackageObjects() if jpackages.isPendingReconfiguration()]

#############################################################
######################  DOMAINS  ############################
#############################################################

    def getDomainObject(self,domain,qualityLevel=None):
        """
        Get provided domain as an object
        """
        self._init()
        if qualityLevel==None:
            for item in self.domains:
                if item.domainname.lower()==domain.lower().strip():
                    return item
        else:
            return Domain(domain,qualityLevel)
        
        raise RuntimeError("Could not find jpackages domain %s" % domain)

    def getDomainNames(self):
        """
        Returns a list of all domains present in the sources.cfg file
        """
        self._init()
        result=[]
        for item in self.domains:
            result.append(item.domainname)
        return result


############################################################
###################  GET PATH FUNCTIONS  ###################
############################################################

    def getJPActionsPath(self,domain,name,instance,fromtmp=False):
        """
        Returns the metadatapath for the provided jpackages
        if fromtmp is True, then tmp directorypath will be returned

        @param domain:  string - The domain of the jpackages
        @param name:    string - The name of the jpackages
        @param fromtmp: boolean
        """
        if fromtmp:
            self._metadatadirTmp
            return j.system.fs.joinPaths(self._metadatadirTmp,domain,name,str(instance),"actions")
        else:
            return j.system.fs.joinPaths(j.dirs.packageDir, "instance", domain,name,str(instance),"actions")


    def getJPActiveInstancePath(self,domain,name,instance,fromtmp=False):
        """
        Returns the metadatapath for the provided jpackages in active mode

        @param domain:  string - The domain of the jpackages
        @param name:    string - The name of the jpackages
        @param fromtmp: boolean
        """
        if fromtmp:
            self._metadatadirTmp
            p=j.system.fs.joinPaths(self._metadatadirTmp,domain,name,str(instance))
        else:
            p=j.system.fs.joinPaths(j.dirs.packageDir, "instance", domain,name,str(instance))
        # j.system.fs.createDir(j.system.fs.joinPaths(p,"hrdactive"))
        return p


    def getJPActiveHRDPath(self,domain,name,instance,fromtmp=False):
        """
        Returns the metadatapath for the provided jpackages
        if fromtmp is True, then tmp directorypath will be returned

        @param domain:  string - The domain of the jpackages
        @param name:    string - The name of the jpackages
        @param version: string - The version of the jpackages
        @param fromtmp: boolean
        """
        if fromtmp:
            self._metadatadirTmp
            return j.system.fs.joinPaths(self._metadatadirTmp,domain,name,str(instance),"hrdactive")
        else:
            return j.system.fs.joinPaths(j.dirs.packageDir, "instance", domain,name,str(instance),"hrdactive")

    def getMetadataPath(self,domain,name,version):
        """
        Returns the metadatapath for the provided jpackages for active state

        @param domain:  string - The domain of the jpackages
        @param name:    string - The name of the jpackages
        @param version: string - The version of the jpackages
        @param fromtmp: boolean
        """
        return j.system.fs.joinPaths(j.dirs.packageDirMD, domain,name,version)

    def getDataPath(self,domain,name,version):
        """
        Returns the filesdatapath for the provided jpackages
        @param domain:  string - The domain of the jpackages
        @param name:    string - The name of the jpackages
        @param version: string - The version of the jpackages
        """        
        return j.system.fs.joinPaths(self.packageDirFiles, domain,name,version)

    def getMetaTarPath(self, domainName):
        """
        Returns the metatarsdatapath for the provided domain
        """
        return j.system.fs.joinPaths(j.dirs.packageDir, "metatars", domainName)


############################################################
######################  CACHING  ###########################
############################################################

    _getcache = {}

    def _deleteFromCache(self, domain, name, version):
        #called by a package when we call delete on it so it can be garbage collected
        key = '%s%s%s' % (domain, name, version)
        self._getcache.remove(key)



############################################################
##########################  FIND  ##########################
############################################################

    def findNewest(self, domain="",name="", minversion="",maxversion="",platform=None, returnNoneIfNotFound=False):
        """
        Find the newest jpackages which matches the criteria
        If more than 1 jpackages matches -> error
        If no jpackages match and not returnNoneIfNotFound -> error
        @param name:       string - The name of jpackages you are looking for
        @param domain:     string - The domain of the jpackages you are looking for
        @param minversion: string - The minimum version the jpackages must have
        @param maxversion: string - The maximum version the jpackages can have
        @param platform:   string - Which platform the jpackages must run on
        @param returnNoneIfNotFound: boolean - if true, will return None object if no jpackages have been found
        """
        results=self.find(domain=domain,name=name)

        # results=[]
        # for item in results0:    
        #     if item.supportsPlatform(platform=None):
        #         results.append(item)

        namefound=""
        domainfound=""
        minversion=minversion.strip()
        maxversion=maxversion.strip()
        if minversion=="":
            minversion="0"
        if maxversion=="" or maxversion=="0":
            maxversion="100.100.100"
        #look for duplicates
        for jp in results:
            if namefound=="":
                namefound=jp.name
            if domainfound=="":
                domainfound=jp.domain
            if jp.domain != domainfound or jp.name != namefound:
                packagesStr="\n"
                for jp2 in results:
                    packagesStr="    %s\n" % str(jp2)
                raise RuntimeError("Found more than 1 jpackages matching the criteria.\n %s" % packagesStr)
        #check for version match
        if len(results)==0:
            if returnNoneIfNotFound:
                return None
            raise RuntimeError("Did not find jpackages with criteria domain:%s, name:%s, platform:%s (independant from version)" % (domain,name,platform))

        # filter packages so they are between min and max version bounds
        result=[jp for jp in results if self._getVersionAsInt(minversion)<=self._getVersionAsInt(jp.version)<=self._getVersionAsInt(maxversion)]
        result.sort(lambda jp1, jp2: - int(self._getVersionAsInt(jp1.version) - self._getVersionAsInt(jp2.version)))
        if not result:
            if returnNoneIfNotFound:
                return None
            j.events.inputerror_critical("Did not find jpackages with criteria domain:%s, name:%s, minversion:%s, maxversion:%s, platform:%s" % (domain,name,minversion,maxversion,platform),"jpackages.findfirst")
        return result[0]


    def findByName(self,name):
        '''
        name is part of jpackage, if none found return None, if more than 1 found raise error, name is part of name
        '''
        # if name.find("*")==-1:
        #     name+="*"
        res=self.find(name=name,domain=None,interactive=False,onlyone=True)
        if len(res)>1:
            j.events.opserror_critical("Found more than 1 jpackage with name '%s' cannot continue, only 1 allowed.\n%s"%(name,res))
        return res[0]
    
    def find(self, domain=None,name=None , version="", platform=None,onlyone=False,installed=None,instance=None,expandInstances=True,interactive=True):
        """ 
        @domain, if none will ask for domain

        """        

        def raiseError(msg,domain,name,version,platform,installed,instance):
            msg2="Jpackage find failed for following arguments\n"
            msg2+="- domain:%s\n"%domain
            msg2+="- name:%s\n"%name
            msg2+="- version:%s\n"%version
            msg2+="- platform:%s\n"%platform
            msg2+="- installed:%s\n"%installed
            msg2+="- instance:%s\n"%instance
            msg2+="ERROR:\n%s\n"%msg
            j.events.inputerror_critical(msg2,"jpackage.find")

        self._init()
        if interactive and domain==None:
            domains=j.console.askChoiceMultiple(j.packages.getDomainNames())
            result=[]
            for domain in domains:
                result+=self.find(domain=domain,name=name , version=version, platform=platform,onlyone=onlyone,installed=installed)
            return result

        if interactive and name==None:
            name = j.console.askString("Please provide the name or part of the name of the package to search for (e.g *extension* -> lots of extensions)")

        res = self._find(domain=domain, name=name, version=version)     
        
        if res==[]:
            raiseError('No packages found, did you forget to run "jpackage mdupdate"?',domain,name,version,platform,installed,instance)

        if installed==False and instance != None:
            msg="Cannot find a jpackage which is not installed and a instance specified (method find got installed==False & instance specified)."
            raiseError(msg,domain,name,version,platform,installed,instance)

        if installed==True:
            res=[item for item in res if item.isInstalled(hrdcheck=False)]

        if installed==False:
            res=[item for item in res if item.isInstalled(hrdcheck=False)==False]

        if instance != None and len(res)>1:
            msg="Cannot find a jpackage for specified instance when more than 1 candidate found, specify domain & name & version more specific"
            raiseError(msg,domain,name,version,platform,installed,instance)

        if expandInstances:
            #now check if there are instances
            res2=[]
            for jp in res:
                root=j.system.fs.joinPaths(j.dirs.packageDir, "instance", jp.domain,jp.name)
                if j.system.fs.exists(path=root):
                    dirs=j.system.fs.listDirsInDir(root,False,True)
                    for instancename in dirs:
                        jp2=copy.copy(jp)
                        jp2.instance=instancename
                        res2.append(jp2)
                else:
                    res2.append(jp)
            res=res2

            if instance != None:
                res=[item for item in res if str(item.instance)==instance]       

        #sort jpackages
        tosortmeta={}
        for item in res:
            tosortmeta["%s_%s_%s_%s"%(item.name,item.domain,item.version,item.instance)]=item
        tosort=list(tosortmeta.keys())
        tosort.sort()
        res=[]
        for sortedkey in tosort:
            res.append(tosortmeta[sortedkey])

        if onlyone:
            if len(res) > 1:
                res = [j.console.askChoice(res, "Multiple packages found, please choose one")]

        return res

    def _find(self, domain="",name="", version=""):
        """
        Tries to find a package based on the provided criteria
        You may also use a wildcard to provide the name or domain (*partofname*)
        @param domain:  string - The name of jpackages domain, when using * means partial name
        @param name:    string - The name of the jpackages you are looking for, when using * means partial name
        @param version: string - The version of the jpackages you are looking for
        """
        
        j.logger.log("Find jpackages domain:%s name:%s version:%s" %(domain,name,version))
        #work with some functional methods works faster than doing the check everytime
        def findPartial(pattern,text):
            pattern=pattern.replace("*","")
            if text.lower().find(pattern.lower().strip()) != -1:
                return True
            return False

        def findFull(pattern,text):
            return pattern.strip().lower()==text.strip().lower()

        def alwaysReturnTrue(pattern,text):
            return True

        domainFindMethod=alwaysReturnTrue
        nameFindMethod=alwaysReturnTrue
        versionFindMethod=alwaysReturnTrue

        if domain:
            if domain.find("*") != -1:
                domainFindMethod=findPartial
            else:
                domainFindMethod=findFull
        if name:
            if name.find("*") != -1:
                nameFindMethod=findPartial
            else:
                nameFindMethod=findFull
        if version:
            if version.find("*") != -1:
                versionFindMethod=findPartial
            else:
                versionFindMethod=findFull

        result=[]
        
        for p_domain, p_name, p_version in self._getJPackageTuples():
            # print (p_domain, p_name, p_version)
            if domainFindMethod(domain,p_domain) and nameFindMethod(name,p_name) and versionFindMethod(version,p_version):
                result.append([p_domain, p_name, p_version])

        result2=[]
        for item in result:
                result2.append(self.get(item[0],item[1], item[2]))
        return result2

    # Used in getJPackageObjects and that is use in find
    def _getJPackageTuples(self):
        self._init()
        res = list()
        domains=self.getDomainNames()
        for domainName in domains:
            domainpath=j.system.fs.joinPaths(j.dirs.packageDirMD, domainName)
            
            if j.system.fs.exists(domainpath): #this follows the link
                packages= [p for p in j.system.fs.listDirsInDir(domainpath,dirNameOnly=True) if p != '.hg'] # skip hg file
                for packagename in packages:
                    packagepath=j.system.fs.joinPaths(domainpath,packagename)
                    versions=j.system.fs.listDirsInDir(packagepath,dirNameOnly=True)
                    for version in versions:
                        hrdfile = j.system.fs.joinPaths(packagepath, version, 'hrd', 'main.hrd')
                        if j.system.fs.exists(hrdfile):
                            res.append([domainName,packagename,version])

        return res

    def getJPackageObjects(self, platform=None, domain=None):
        """
        Returns a list of jpackages objects for specified platform & domain
        """
        self._init()
        packageObjects = [self.get(*p) for p in self._getJPackageTuples()]
        if platform==None:
            return [p for p in packageObjects if (domain == None or p.domain == domain)]

        def hasPlatform(package):
            return any([supported in j.system.platformtype.getParents(platform) for supported in package.supportedPlatforms])

        return [p for p in packageObjects if hasPlatform(p) and (domain == None or p.domain == domain)]

    def getPackagesWithBrokenDependencies(self):
        return [p for p in j.packages.find('*') if len(p.getBrokenDependencies()) > 0]


############################################################
#################  UPDATE / PUBLISH  #######################
############################################################

    def updateAll(self):
        '''
        Updates all installed jpackages to the latest builds.
        The latest meta information is retrieved from the repository and based on this information,
        The install packages that have a buildnr that has been outdated our reinstall, thust updating them to the latest build.
        '''
        self._init()
        # update all meta information:
        self.updateMetaData()
        # iterate over all install packages and install them
        # only when they are outdated will they truly install
        for p in self.getInstalledPackages():
            p.install()
    
    def updateMetaDataAll(self,force=False):
        """
        Updates the metadata information of all jpackages
        This used to be called updateJPackage list
        @param is force True then local changes will be lost if any
        """
        self._init()
        self.updateMetaData("",force)

    def mergeMetaDataAll(self,):
        """
        Tries to merge the metadata information of all jpackages with info on remote repo.
        This used to be called updateJPackage list
        """        
        self._init()
        j.packages.mergeMetaData("")        
        
    def updateMetaDataForDomain(self,domainName=""):
        """
        Updates the meta information of specific domain
        This used to be called updateJPackage list
        """
        self._init()
        if domainName=="":
            domainName = j.console.askChoice(j.packages.getDomainNames(), "Please choose a domain")
        j.packages.getDomainObject(domainName).updateMetadata("")        


    def linkMetaData(self,domain=""):
        """
        Does an link of the meta information repo for each domain
        """
        self._init()
        self.resetState()
        if domain != "":
            j.logger.log("link metadata information for jpackages domain %s" % domain, 1)
            d=self.getDomainObject(domain)
            d.linkMetadata()
        else:
            domainnames=self.getDomainNames()            
            for domainName in domainnames:
                self.linkMetaData(domainName)

    def switchMetaData(self,toQualitylevel,domain="",disableDebug=False):
        self._init()
        # self.resetState()
        if domain != "":
            j.logger.log("Switch metadata quality level for jpackages domain %s" % domain, 1)
            d=self.getDomainObject(domain)
            # from IPython import embed
            # print "DEBUG NOW switchMetaData"
            # embed()
            
        else:
            domainnames=self.getDomainNames()            
            for domainName in domainnames:
                self.switchMetaData(toQualitylevel, domainName,setDebugOff)

    def _finddomain(self,name):
        for cat in j.system.fs.listDirsInDir("/opt/code/", recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
            for dname in j.system.fs.listDirsInDir("/opt/code/%s"%cat, recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
                if dname.find("__jp_") != -1:
                    dname2=dname.split("__jp_",1)[1]
                    if dname2.lower().strip()==name.lower().strip():
                        return "/opt/code/%s/%s"%(cat,dname)
        raise RuntimeError("could not find domain for name:'%s'"%name)

    def disableDebugMetaData(self,qualitylevel,domain=""):
        self._init()        
        # self.resetState()
        if domain != "":
            j.logger.log("Disable debug mode for jpackages domain %s" % domain, 1)

            path=self._finddomain(domain)
            # print "JPACKAGEDOM:%s"%path
            dpath="%s/%s/"%(path,qualitylevel)
            for path in j.system.fs.listFilesInDir(dpath,True,"main.hrd"):
                hrd=j.core.hrd.getHRD(path)
                hrd.set("jp.debug",0)
        else:
            domainnames=self.getDomainNames()            
            for domainName in domainnames:
                self.disableDebugMetaData(domainName)

    def updateMetaData(self,domain="",force=False):
        """
        Does an update of the meta information repo for each domain
        """
        self._init()
        # self.resetState()
        if domain != "":
            j.logger.log("Update metadata information for jpackages domain %s" % domain, 1)
            d=self.getDomainObject(domain)
            d.updateMetadata(force=force)
        else:
            domainnames=self.getDomainNames()            
            for domainName in domainnames:
                self.updateMetaData(domainName, force=force)

    def mergeMetaData(self,domain="", commitMessage=''):
        """
        Does an update of the meta information repo for each domain
        """
        self._init()
        if not j.application.shellconfig.interactive:
            if commitMessage == '':
                raise RuntimeError('Need commit message')

        if domain != "":
            j.logger.log("Merge metadata information for jpackages domain %s" % domain, 1)
            d=self.getDomainObject(domain)
            d.mergeMetadata(commitMessage=commitMessage)
        else:
            for domainName in self.getDomainNames():
                self.mergeMetaData(domainName, commitMessage=commitMessage)

    def _getQualityLevels(self,domain):
        cfg=self.sourcesConfig        
        bitbucketreponame=cfg.getValue( domain, 'bitbucketreponame')
        bitbucketaccount=cfg.getValue( domain, 'bitbucketaccount')      
        qualityLevels=j.system.fs.listDirsInDir(j.system.fs.joinPaths(j.dirs.codeDir,bitbucketaccount,bitbucketreponame),dirNameOnly=True)        
        qualityLevels=[item for item in qualityLevels if item != ".hg"]
        return qualityLevels
    
    def _getMetadataDir(self,domain,qualityLevel=None,descr=""):
        cfg=self.sourcesConfig        
        bitbucketreponame=cfg.getValue( domain, 'bitbucketreponame')
        bitbucketaccount=cfg.getValue( domain, 'bitbucketaccount')      
        if descr=="":
            descr="please select your qualitylevel"
        if qualityLevel==None or qualityLevel=="":
            qualityLevel=j.console.askChoice(self._getQualityLevels(domain),descr)
        return j.system.fs.joinPaths(j.dirs.codeDir,bitbucketaccount,bitbucketreponame,qualityLevel)      

    def metadataDeleteQualityLevel(self, domain="",qualityLevel=None):
        """
        Delete a quality level 
        """
        self._init()
        if domain != "":
            j.logger.log("Delete quality level %s for %s." % (qualityLevel,domain), 1)
            metadataPath=self._getMetadataDir(domain,qualityLevel)            
            j.system.fs.removeDirTree(metadataPath)
        else:
            if j.application.shellconfig.interactive:
                domainnames=j.console.askChoiceMultiple(j.packages.getDomainNames())
            else:
                domainnames=self.getDomainNames()
            for domainName in domainnames:
                self.metadataDeleteQualityLevel(domainName,qualityLevel)


    def metadataCreateQualityLevel(self, domain="",qualityLevelFrom=None,qualityLevelTo=None,force=False,link=True):
        """
        Create a quality level starting from the qualitylevelFrom e.g. unstable to beta
        @param link if True will link the jpackages otherwise copy
        @param force, will delete the destination
        """
        self._init()
        if domain != "":
            j.logger.log("Create quality level for %s from %s to %s" % (domain,qualityLevelFrom,qualityLevelTo), 1)
            metadataFrom=self._getMetadataDir(domain,qualityLevelFrom,"please select your qualitylevel where you want to copy from for domain %s." % domain)
            if qualityLevelTo==None or qualityLevelTo=="":
                qualityLevelTo=j.console.askString("Please specify qualitylevel you would like to create for domain %s" % domain)                
            metadataTo=self._getMetadataDir(domain,qualityLevelTo)
            dirsfrom=j.system.fs.listDirsInDir(metadataFrom)
            if j.system.fs.exists(metadataTo):
                if force or j.console.askYesNo("metadata dir %s exists, ok to remove?" % metadataTo):
                    j.system.fs.removeDirTree(metadataTo)
                else:
                    raise RuntimeError("Cannot continue to create metadata for new qualitylevel, because dest dir exists")
            j.system.fs.createDir(metadataTo)
            for item in dirsfrom:
                while j.system.fs.isLink(item):
                    #look for source of link                
                    item=j.system.fs.readlink(item)
                dirname=j.system.fs.getDirName( item+"/", lastOnly=True)
                if link:
                    j.system.fs.symlink( item,j.system.fs.joinPaths(metadataTo,dirname),overwriteTarget=True)
                else:
                    j.system.fs.copyDirTree(item, j.system.fs.joinPaths(metadataTo,dirname), keepsymlinks=False, eraseDestination=True)
        else:
            if j.application.shellconfig.interactive:
                domainnames=j.console.askChoiceMultiple(j.packages.getDomainNames())
            else:
                domainnames=self.getDomainNames()
            for domainName in domainnames:
                self.metadataCreateQualityLevel(domainName,qualityLevelFrom,qualityLevelTo,force,link)

                
   
    def publishMetaDataAsTarGz(self, domain="",qualityLevel=None):
        """
        Compresses the meta data of a domain into a tar and upload that tar to the bundleUpload server.
        After this the that uptain there metadata as a tar can download the latest metadata.
        """
        self._init()
        if domains==[]:
            domains=j.console.askChoiceMultiple(j.packages.getDomainNames(), "Please select a domain")

        if len(domains)>1:
            for domain in domains:
                self.publishMetaDataAsTarGz(domain=domain,qualityLevel=qualityLevel)
        else:
            j.logger.log("Push metadata information for jpackages domain %s to reposerver." % domain, 1)
            if qualityLevel=="all":
                for ql in self._getQualityLevels(domain):
                    d = self.getDomainObject(domain,qualityLevel=ql)
                    d.publishMetaDataAsTarGz()                
            else:
                d = self.getDomainObject(domain,qualityLevel=qualityLevel)
                d.publishMetaDataAsTarGz()
           
    def publish(self, commitMessage,domain=""):
        """
        Publishes all domains' bundles & metadata (if no domain specified)
        @param commitMessage: string - The commit message you want to assign to the publish
        """
        self._init()
        if domain=="":
            for domain in j.packages.getDomainNames():
                self.publish( commitMessage=commitMessage,domain=domain)
        else:
            domainobject=j.packages.getDomainObject(domain)
            domainobject.publish(commitMessage=commitMessage)

    def publishAll(self, commitMessage=None):
        """
        Publish metadata & bundles for all domains, for more informartion see publishDomain
        """
        self._init()
        if not commitMessage:
            commitMessage = j.console.askString('please enter a commit message')
        for domain in j.packages.getDomainNames():
            self.publishDomain(domain, commitMessage=commitMessage)

    def publishDomain(self, domain="", commitMessage=None):
        """
        Publish metadata & bundles for a domain. 
        To publish a domain means to make your local changes to the corresponding domain available to other users.
        A domain can be changed in the following ways: a new package is created in it, a package in it is modified, a package in it is deleted.
        To make the changes available to others the new metadata is uploaded to the mercurial servers and for the packages whos files 
        have been modified,
        new bundles are created and uploaded to the blobstor server
        """
        self._init()
        if domain=="":
            domain=j.console.askChoice(j.packages.getDomainNames(), "Please select a domain")
        self.getDomainObject(domain)._ensureDomainCanBeUpdated()
        self.getDomainObject(domain).publish(commitMessage=commitMessage)


##########################################################
####################  RECONFIGURE  #######################
##########################################################

    def _setHasPackagesPendingConfiguration(self, value=True):
        file = j.system.fs.joinPaths(j.dirs.baseDir, 'cfg', 'jpackages', 'reconfigure.cfg')
        if not j.system.fs.exists(file):
            ini_file = j.tools.inifile.new(file)
        else:
            ini_file = j.tools.inifile.open(file)

        if not ini_file.checkSection('main'):
            ini_file.addSection('main')


        ini_file.setParam("main","hasPackagesPendingConfiguration", "1" if value else "0")
        ini_file.write()

    def _hasPackagesPendingConfiguration(self):
        file = j.system.fs.joinPaths(j.dirs.baseDir, 'cfg', 'jpackages', 'reconfigure.cfg')
        if not j.system.fs.exists(file):
            return False
        ini_file = j.tools.inifile.open(file)

        if ini_file.checkSection('main'):
            return ini_file.getValue("main","hasPackagesPendingConfiguration") == '1'

        return False

    def runConfigurationPending(self):
        #@todo prob need to redo this and use redis or so, this is completely reloading all
        # from IPython import embed
        # print "DEBUG NOW runConfigurationPending"
        # embed()
        
        if not self._hasPackagesPendingConfiguration():
            return

        # Get all packages that need reconfiguring and reconfigure them
        # We store the state to reconfigure them in their state files
        configuredPackages = set()
        currentPlatform = PlatformType.findPlatformType()

        def configure(package):
            # If already processed return
            if package in configuredPackages:
                return True
            configuredPackages.add(package)

            # first make sure depending packages are configured
            for dp in package.getDependencies(recursive=False, platform=currentPlatform):
                if not configure(dp):
                    return False

            # now configure the package
            if package.isPendingReconfiguration():
                j.logger.log("jpackages %s %s %s needs reconfiguration" % (package.domain,package.name,package.version),3)
                try:
                    package.configure()
                except:
                    j.debugging.printTraceBack('Got error while reconfiguring ' + str(package))
                    if j.console.askChoice(['Skip this one', 'Go to shell'], 'What do you want to do?') == 'Skip this one':
                        return True
                    else:
                        return False
            return True


        pendingPackages = self.getPendingReconfigurationPackages()
        hasPendingConfiguration = False
        for p in pendingPackages:
            if not configure(p):
                hasPendingConfiguration = True
                break

        self._setHasPackagesPendingConfiguration(hasPendingConfiguration)


############################################################
################  SUPPORTING FUNCTIONS  ####################
############################################################

    def _getVersionAsInt(self,version):
        """
        @param version is string
        """
        version=version.strip()
        if version.find(",") != -1:
            raise RuntimeError("version string can only contain numbers and . e.g. 1.1.1")
        if version=="":
            version="0"
        if version.find(".") != -1:
            versions=version.split(".")
        else:
            versions=[version]
        if len(versions)>4:
            raise RuntimeError("max level of versionlevels = 4 e.g. max 1.1.1.1")
        #make sure always 4 levels of versions for comparison
        while(len(versions)<4):
            versions.append("0")
        result=0
        for counter in range(0,len(versions)):
            level=len(versions)-counter-1
            if versions[counter]=="":
                versions[counter]="0"
            result=int(result+(math.pow(1000,level)*int(versions[counter].strip())))                
        return result

    def pm_getJPackageConfig(self, jpackagesMDPath):
        return JPackageConfig(jpackagesMDPath)

    def makeDependencyGraph(self):
        '''
        Creates a graphical visualization of all dependencies between the JPackackages of all domains.
        This helps to quickly view and debug the dependencies and avoid errors.
        The target audience are the developers of accross groups and domains that depend on each others packages.
        
        The graph can be found here:   
        /opt/qbase5/var/jpackages/metadata/dependencyGraph.png
        
        Notes:  
        The graph omits the constraints, such as version numbers and platform.
        
        For completeness, a second graph is created that shows packages without andy dependencies (both ways). 
        See: dependencyGraph_singleNodes.png
        '''

        from pygraphviz import AGraph  #import only here to avoid overhead
        
        def _getPackageTagName(obj, separator=' - '):
            n = obj.name
            #n += '\\n'
            #n  += obj.domain
            return n

        j.console.echo("Making Dependency graph ... please wait.")
    
        platform = PlatformType.getByName('generic')
           
        g=AGraph(strict=True,directed=True, compound=True)
        
        g.graph_attr['rankdir']='LR'
        g.graph_attr['ratio']=1.3
    
        #Generate the graph
        for pack in j.packages.getJPackageObjects():
            dn= 'cluster_'+pack.domain
            s= g.add_subgraph(name = dn)
            s.add_node(_getPackageTagName(pack))
            
            x=g.get_node(_getPackageTagName(pack))
            x.attr['label']=_getPackageTagName(pack)
            
            depList= pack.getDependencies(platform, recursive=False)
            for dep in depList:
                g.add_node(_getPackageTagName(dep))
                g.add_edge(_getPackageTagName(pack),_getPackageTagName(dep))
       
        #Separate nodes with and without links
        singleNodes=[]
        linkedNodes=[]
        for n in g.nodes():
            c=[]
            c=g.neighbors(n)
            if c==[]:
                singleNodes.append(n)
            else:
                linkedNodes.append(n)
     
        #Add the domain name to the graph
        for pack in j.packages.getJPackageObjects():
            n=pack.domain
            dn= 'cluster_'+pack.domain       
    
            s= g.add_subgraph(name=dn)
            s.add_node(n)
                        
            x=g.get_node(n)
            x.attr['label']=n
            x.attr['style']='filled'
            x.attr['shape']='box'
            
        #Create a second version, for the graph of single nodes
        stemp=g.to_string()        
        s=AGraph(stemp)    
        
        for n in singleNodes:
            g.delete_node(n)
    
        for n in linkedNodes:
            s.delete_node(n)
        
        g.layout(prog='dot')    
        graphPath = j.system.fs.joinPaths(j.dirs.packageDirMD,'dependencyGraph.png')
        g.draw(graphPath)
    
        s.layout(prog='dot')
        graphPath = j.system.fs.joinPaths(j.dirs.packageDirMD,'dependencyGraph_singleNodes.png')
        s.draw(graphPath)

        j.console.echo("Dependency graph successfully created. Open file at /opt/qbase5/var/jpackages/metadata/dependencyGraph.png")

############################################################
################  RECOVERY FUNCTIONS  ####################
############################################################
    def uploadLocalJpackagesToBlobStor(self,blobservername="jpackages_remote",history=False):
        for jp in self.getJPackageObjects():
            if history==False:
                jp.uploadExistingBlobs(blobservername)
            else:
                jp.uploadExistingBlobsFromHistory(blobservername)


    def checkJpackagesExistsOnRemoteBlobStor(self):
        notfound2=[]
        print("JPACKAGES WITH INCOMPLETE BLOBSTOR")
        for jp in self.getJPackageObjects():
            notfound=jp.checkExistingBlobs("jpackages_remote")
            if len(notfound)>0:
                notf=[jp.domain,jp.name,jp.buildNr,",".join(notfound)]
                print(notf)
                notfound2.append(notf)
        return notfound2

