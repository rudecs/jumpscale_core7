
from JumpScale import j
import JumpScale.baselib.vcs

class RecipeItem(object):
    '''Ingredient of a CodeRecipe'''
    def __init__(self, repoinfo,source, destination,platform="generic",type="base",tags="",recipe=None):
        """
        @param types sitepackages, root, base, etc, tmp,bin
        @param tagslabels: e.g. config as str
        """
        self.repoinfo=repoinfo
        self.source = source.strip().strip("/")
        self.recipe=recipe

        self.destination=destination.strip().strip("/")
        if self.destination=="":
            self.destination=self.source

        if platform=="":
            platform="generic"

        self.platform=platform

        self.type=type.lower().strip()

        self.systemdest = j.packages.getTypePath(self.type, self.destination,jp=self.recipe.jp)
        self.tags=tags
        
        # determine supported platforms 
        hostPlatform = j.system.platformtype.myplatform
        supportedPlatforms = list()

        supportedPlatforms = j.system.platformtype.getParents(hostPlatform)
        if not platform:
            self._isPlatformSupported = hostPlatform in supportedPlatforms
        else:
            self._isPlatformSupported = self.platform in supportedPlatforms

    def _log(self,message,category="",level=5):
        message="recipeitem:%s-%s  %s" % (self.source,self.destination,message)
        category="recipeitem.%s"%category
        category=category.rstrip(".")
        j.packages.log(message,category,level)     

    def getSource(self):
        account=self.repoinfo.get("jp.code.account")
        repo=self.repoinfo.get("jp.code.repo")
        branch=self.repoinfo.get("jp.code.branch")
        provider=self.repoinfo.get("jp.code.provider")
        if branch=="":
            branch="default"
        return j.system.fs.joinPaths(j.dirs.codeDir,provider,account,repo, self.source)

    def exportToSystem(self,force=True):
        '''
        Copy files from coderepo to destination, without metadata of coderepo
        This is only done when the recipe item is relevant for our platform
        '''
        self._log("export to system.","export")

        if self._isPlatformSupported:
            source = self.getSource()
            if self.systemdest==None:
                j.events.inputerror_critical("System destination was not defined, cannot export:%s"%self)
            destination = self.systemdest
            print("export:%s to %s"%(source,destination))
            if j.system.fs.isLink(destination):
                j.system.fs.remove(destination)   
                j.dirs.removeProtectedDir(destination)
            else:
                if j.system.fs.exists(destination) and force==False:
                    if j.application.shellconfig.interactive:                            
                        if not j.gui.dialog.askYesNo("\nDo you want to overwrite %s" % destination, True):
                            j.gui.dialog.message("Not overwriting %s, item will not be exported" % destination)
                            return        
                self._removeDest(destination)  
            if j.system.fs.isFile(source):
                j.system.fs.copyFile(source, destination,skipProtectedDirs=True)
                # self._setSecurityFromSource(source,destination)
            else:
                j.system.fs.copyDirTree(source, destination,skipProtectedDirs=True)
                             
        
    def _copy(self, src, dest):
        if not j.system.fs.exists(src):
            raise RuntimeError("Cannot find:%s for recipeitem:%s"%(src,self))
        
        if j.system.fs.isFile(src):
            destDir = j.system.fs.getDirName(dest)
            j.system.fs.createDir(destDir,skipProtectedDirs=True)
            j.system.fs.copyFile(src, dest,skipProtectedDirs=True)
        elif j.system.fs.isDir(src):            
            j.system.fs.copyDirTree(src, dest,skipProtectedDirs=True)
        else:
            raise RuntimeError("Cannot handle destination %s %s\n Did you codecheckout your code already? Code was not found to package." % (src, dest))

    def codeToFiles(self, jpackage):
        """
        copy code from repo's (using the recipes) to the file location for packaging
        this is done per platform as specified in recipe, if not specified then generic
        """

        self._log("package code to files for %s"%(jpackage),category="codetofiles")        
        src = self.getSource()        
        platformFilesPath = jpackage.getPathFilesPlatform(self.platform)
        dest = j.system.fs.joinPaths(platformFilesPath, "cr_%s"%self.type ,self.destination)
        self._removeDest(dest)
        self._copy(src, dest)
        
        
    def linkToSystem(self,force=False):
        '''
        link parts of the coderepo to the destination and put this  entry in the protected dirs section so data cannot be overwritten by jpackages
        '''
        self._log("link to system",category="link")
        force=True #@todo will have to change, now always true
        
        if self.type=="config":
            return self.exportToSystem()
        if self._isPlatformSupported:
            source = self.getSource()        
            destination = self.systemdest
            if self.systemdest==None:
                j.events.inputerror_critical("System destination was not defined, cannot export:%s"%self)


            if self.tags.labelExists("config"):
                print("CONFIG:%s"%self)
                self.exportToSystem(force=force)
            else:
                print("link:%s to %s"%(source,destination))
                if j.system.fs.isLink(destination):
                    j.system.fs.remove(destination)   
                else:
                    if j.system.fs.exists(destination) and force==False:
                        if j.application.shellconfig.interactive:                            
                            if not j.gui.dialog.askYesNo("\nDo you want to overwrite %s" % destination, True):
                                j.gui.dialog.message("Not overwriting %s, it will not be linked" % destination)
                                return        
        
                    self._removeDest(destination)
                if not j.system.fs.exists(path=source):
                    raise RuntimeError("Cannot find source to put link to, link was from %s to %s"%(source,destination))
                j.system.fs.symlink(source, destination)
                # self._setSecurityFromSource(source,destination)
                j.dirs.addProtectedDir(destination)

    # def _setSecurityFromSource(self,src,dest):
    #     stat=j.system.fs.statPath(src)
    #     j.system.fs.chmod(dest,stat.st_mode)
    #     print "%s %s" % (stat.st_mode,j.system.fs.statPath(src).st_mode)


    def addToProtectedDirs(self):
        if not self.tags.labelExists("config"):
            if self.systemdest==None:
                j.events.inputerror_critical("System destination was not defined, cannot export:%s"%self)
            j.dirs.addProtectedDir(self.systemdest)

    def removeFromProtectedDirs(self):
        if not self.tags.labelExists("config"):
            if self.systemdest==None:
                j.events.inputerror_critical("System destination was not defined, cannot export:%s"%self)
            j.dirs.removeProtectedDir(self.systemdest)

    def unlinkSystem(self,force=False):
        '''
        unlink the system, remove the links and copy the content instead
        '''
        self._log("unlink system",category="link")
        
        if self.type=="config":
            return 
        if self.systemdest==None:
            j.events.inputerror_critical("System destination was not defined, cannot export:%s"%self)
        if j.system.fs.isLink(self.systemdest):
            j.system.fs.remove(self.systemdest)
            j.dirs.removeProtectedDir(self.systemdest)

        self.exportToSystem(force=force)
        
    def _removeDest(self, dest):
        """ Remove a destionation file or directory."""
        isFile = j.system.fs.isFile
        isDir = j.system.fs.isDir
        removeFile = j.system.fs.remove
        removeDirTree = j.system.fs.removeDirTree
        exists = j.system.fs.exists

        if not exists(dest):
            return
        elif isFile(dest):
            removeFile(dest)
        elif isDir(dest):
            removeDirTree(dest)
        else:
            raise RuntimeError("Cannot remove destination of unknown type '%s'" % dest)

    def __str__(self):
        return "from:%s to:%s type:%s platf:%s tags:%s" %(self.source,self.destination,self.type,self.platform,self.tags)
    
    def __repr__(self):
        return self.__str__()


class CodeManagementRecipe:
    '''
    Recipe providing guidelines how to cook a JPackage from source code in a repo, is populated from a config file
    '''
    def __init__(self,hrdpath,configpath,jp=None):
        self._repoconnection = None
        self.configpath=configpath
        self.hrd=j.core.hrd.getHRD(hrdpath)
        self.items = []
        self.jp=jp
        self._process()

    def _getSource(self,source):
        account=self.hrd.get("jp.code.account")
        repo=self.hrd.get("jp.code.repo")
        branch=self.hrd.get("jp.code.branch")
        provider=self.hrd.get("jp.code.provider")
        if repo=="" or account=="":
            raise RuntimeError("cannot define codemgmt recipe with empty account or repo, please adjust: hrd/code.hrd in jpackage dir %s"%self.configpath)
        if branch=="":
            branch="default"

        return j.system.fs.joinPaths(j.dirs.codeDir,provider,account,repo, source)

    def _process(self):
        if self.repoconnection:
            self.repoconnection.init()
        content=j.system.fs.fileGetContents(self.configpath)
        for line in content.split("\n"):
            line=line.strip()
            if line=="" or line[0]=="#":
                continue
            splitted= line.split("|")
            if len(splitted) != 5:
                raise RuntimeError("error in coderecipe config file: %s on line:%s"%(self.configpath,line))
            splitted=[item.strip() for item in splitted]
            source,dest,platform,ttype,tags=splitted
            tags=j.core.tags.getObject(tags)
            if source.find("*") != -1:
                source=source.replace("*","")
                source2=self._getSource(source)
                for item in j.system.fs.listFilesInDir(source2,recursive=False):
                    item=j.system.fs.getBaseName(item)                    
                    source3="%s/%s"%(source,item)
                    source3=source3.replace("//","/")
                    # print "*%s*"%source3
                    idest = j.system.fs.joinPaths(dest, item)                    
                    item=RecipeItem(self.hrd,source=source3, destination=idest,platform=platform,type=ttype,tags=tags,recipe=self)
                    self.items.append(item)                                                
                if tags.labelExists("nodirs"):
                    continue
                for item in j.system.fs.listDirsInDir(source2,recursive=False):
                    item=j.system.fs.getBaseName(item+"/")                    
                    idest = j.system.fs.joinPaths(dest, item)
                    source3="%s/%s"%(source,item)
                    source3=source3.replace("//","/")
                    source3=source3.replace("//","/")
                    # print "*%s*"%source3
                    item=RecipeItem(self.hrd,source=source3, destination=idest,platform=platform,type=ttype,tags=tags,recipe=self)
                    self.items.append(item) 
            else:
                item=RecipeItem(self.hrd,source=source, destination=dest,platform=platform,type=ttype,tags=tags,recipe=self)
                self.items.append(item)


    def export(self):
        '''Export all items from VCS to the system sandbox or other location specifed'''
        for item in self.items:
            item.exportToSystem()
            
    def addToProtectedDirs(self):
        for item in self.items:
            item.addToProtectedDirs()

    def removeFromProtectedDirs(self):
        for item in self.items:
            item.removeFromProtectedDirs()

    def link(self,force=False):
        for item in self.items:
            item.linkToSystem(force=force)    

    def unlink(self,force=False):
        for item in self.items:
            item.unlinkSystem(force=force)    

    # def importFromSystem(self,jpackages):
    #     """
    #     go from system to files section
    #     """
    #     for item in self.items:
    #         item.importFromSystem(jpackages)                

    def package(self, jpackage,*args,**kwargs):
        for item in self.items:
            item.codeToFiles(jpackage)

    def push(self):
        if self.repoconnection:
            self.repoconnection.push()

    def update(self,force=False):
        if self.repoconnection:
            return self.repoconnection.update(force=force)
    
    def pullupdate(self,force=False):
        if self.repoconnection:
            self.repoconnection.update()

    def pullmerge(self):
        if self.repoconnection:
            self.repoconnection.update()

    def commit(self):
        if self.repoconnection:
            self.repoconnection.commit()

    @property
    def repoconnection(self):
        if self._repoconnection:
            return self._repoconnection
        account=self.hrd.get("jp.code.account")
        repo=self.hrd.get("jp.code.repo")
        if repo=="":
            print("repo not filled in, so coderecipe probably not used for %s"%self)
            return

        branch=self.hrd.get("jp.code.branch") or None
        ttype=self.hrd.get("jp.code.type")
        provider=self.hrd.get("jp.code.provider")

        print("getrepo connection: %s %s %s %s"%(provider, account, repo, branch))
        self._repoconnection = j.clients.vcs.getClient(ttype, provider, account, repo)
        return self._repoconnection

    def isDestinationClean(self):
        '''Check whether the final destination is clean (means do the folders exist)

        Returns C{True} if none of the destination folders exist, C{False}
        otherwise.
        '''
        for item in self._items:
            if j.system.fs.exists(item.destination):
                return False

        return True

    def removeFromSystem(self):
        '''Remove all folders the recipe has written to'''
        for item in self._items:
            if j.system.fs.isDir(item.destination):
                j.system.fs.removeDirTree(item.destination)
            else:
                j.system.fs.remove(item.destination)

    def __str__(self):
        s="recipe:\n"
        for item in self.items:
            s+="- %s\n" % item
        return s
    
    def __repr__(self):
        return self.__str__()

