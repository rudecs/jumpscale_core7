from JumpScale import j
import os
import JumpScale.baselib.vcs

class Domain(): 

    """
    is representation of domain
    source can come from tgz or from mercurial
    """

    def __init__(self, domainname,qualityLevel=None): ## Init must come after definition of lazy getters and setters!
        self.domainname  = domainname
        self.initialized = False
        self._vcsclient = None
        self._ensureInitialized(qualityLevel)

    def _ensureInitialized(self,qualityLevel=None):

        if self.initialized:
            return
        
        cfgFilePath = j.system.fs.joinPaths(j.dirs.cfgDir, 'jpackages', 'sources.cfg')
        cfg = j.tools.inifile.open(cfgFilePath)

        self.metadataFromTgz = cfg.getValue(self.domainname, 'metadatafromtgz') in ('1', 'True')        

        if not 'JSBASE' in os.environ:
            self.reponame=cfg.getValue( self.domainname, 'reponame')
            self.account=cfg.getValue( self.domainname, 'account')
            self.provider = 'github'
            self.repotype = 'git'
            if cfg.checkParam(self.domainname, 'type'):
                self.repotype = cfg.getValue(self.domainname, 'type')
            if cfg.checkParam(self.domainname, 'provider'):
                self.provider = cfg.getValue(self.domainname, 'provider')

            if qualityLevel==None:
                self.qualitylevel = cfg.getValue( self.domainname, 'qualitylevel')
            else:
                self.qualitylevel = qualityLevel

            self._sourcePath = self._getSourcePath() #link to source of metadata (the repo's)

        else:
            self.qualitylevel=""
                    
        if self.metadataFromTgz :
            self.metadatadir=j.system.fs.joinPaths(j.dirs.varDir,"jpackages","metadata",self.domainname)
            j.system.fs.createDir(self.metadatadir)            
        else:            
            self.metadatadir = self.getMetadataDir(self.qualitylevel)
        
        self.blobstorremote=cfg.getValue(self.domainname, 'blobstorremote')
        self.blobstorlocal=cfg.getValue(self.domainname, 'blobstorlocal')
        
        self.metadataUpload=cfg.getValue(self.domainname, 'metadataupload')
        self.metadataDownload=cfg.getValue(self.domainname, 'metadatadownload')

        self._metadatadirTmp = j.system.fs.joinPaths(j.dirs.varDir,"tmp","jpackages","md", self.domainname)

        self.initialized = True

    @property
    def vcsclient(self):
        if not self._vcsclient:
            self._vcsclient = j.clients.vcs.getClient(self.repotype, self.provider, self.account, self.reponame)
        return self._vcsclient


    def getJPackageMetadataDir(self, qualitylevel, name, version):
        """
        Get the meta data dir for the JPackage with `name` and `version` on
        `qualitylevel`.

        @param qualitylevel: quality level
        @type qualitylevel: string
        @param name: name of the JPackage
        @type name: string
        @param version: version of the JPackage
        @type version: string
        @return: path of the meta data dir for the JPackage
        @rtype: string
        """        
        metadataDir = self.getMetadataDir(qualitylevel)
        return j.system.fs.joinPaths(metadataDir, name, version)

    def getMetadataDir(self, qualitylevel=None):
        """
        Get the meta data dir for the argument quality level, or for the current
        quality level if no quality level is passed.

        @param qualitylevel: optional quality level to return the metadata dir for
        @type qualitylevel: string
        @return: metadata dir for the argument quality level or the current quality level if no quality level argument is passed
        @rtype: str
        """
        if 'JSBASE' in os.environ:
            return j.system.fs.joinPaths(os.environ['JSBASE'],"jpackages")
        elif self.metadataFromTgz:
            raise NotImplementedError("Getting the metadata dir for a tar-gz "
                    "based domain is not yet supported")
        else:
            # qualitylevel = qualitylevel or self.qualitylevel
            # return j.system.fs.joinPaths(self._sourcePath, qualitylevel)
            return j.system.fs.joinPaths(self._sourcePath, "jpackages")

    def getQualityLevels(self):
        """
        Return the available quality levels for this domain

        @return: the available quality levels for this domain
        @rtype: list(string)
        """
        if 'JSBASE' in os.environ:
            raise RuntimeError("No qualitylevels in sandboxed mode")
        if self.metadataFromTgz:
            raise NotImplementedError("Getting the quality levels for a tar-gz "
                    "based domain is not yet supported")
        else:
            dirs = j.system.fs.listDirsInDir(self._sourcePath, dirNameOnly=True)
            qualitylevels = [d for d in dirs if not d.startswith('.')]
            return qualitylevels

    def _getSourcePath(self):
        if self.metadataFromTgz:
            raise NotImplementedError("Getting the source path for a tar-gz "
                    "based domain is not yet supported")
        else:
            if 'JSBASE' in os.environ:
                raise RuntimeError("No sourcepath in sandboxed mode")
            return self.vcsclient.baseDir

    def saveConfig(self):
        """
        Saves changes to the jpackages config file
        """
        if 'JSBASE' in os.environ:
            raise RuntimeError("No changes allowed in sandboxed mode")        
        cfg = j.tools.inifile.open(j.system.fs.joinPaths(j.dirs.cfgDir, 'jpackages', 'sources.cfg'))
        if not cfg.checkSection(self.domainname):
            cfg.addSection(self.domainname)
        cfg.setParam(self.domainname, 'metadatadownload', self.metadataDownload)
        cfg.setParam(self.domainname, 'metadataupload', self.metadataUpload)
        cfg.setParam(self.domainname, 'metadatafromtgz', int(self.metadataFromTgz))
        cfg.setParam(self.domainname, 'qualitylevel', self.qualitylevel)
        
        #outdated:
        #cfg.setParam(self.domainname, 'metadatabranch', self.metadataBranch)
        #cfg.setParam(self.domainname, 'metadatafrommercurial', self.metadataFromMercurial)

        cfg.write()

    def hasModifiedMetadata(self):
        """
        Checks for the entire domain if it has any modified metadata
        """
        #check mercurial
        if not self.metadataFromTgz:
            return self.vcsclient.hasModifiedFiles()
        else:
            return False

    def hasModifiedFiles(self): #This is the prepared files?
        """
        Checks for the entire domain if it has any modified files
        """
        for jpackages in self.getJPackages():
            if jpackages.hasModifiedFiles():
                return True
        return False

    def _mercurialLinesToPackageTuples(self, changedFiles):
        changedPackages = set()
        for line in changedFiles: # @todo test on windows
                #  exampleline: zookeeper/1.0/jpackages.cfg
                #  exampleline: zookeeper/1.0/tasklets/sometasklet.py
            line=line.replace("\\","/") #try to get it to work on windows
            splitted=line.split('/')
            if len(splitted)>1:
                name    = splitted[1]
                version = splitted[2]
                jpackages = (self.domainname, name, version)
                changedPackages.add(jpackages)
        return list(changedPackages)

    def getJPackageTuplesWithNewMetadata(self):
        hg = self.bitbucketclient.getMercurialClient(self.bitbucketreponame)
        changedFiles = hg.getModifiedFiles()
        
        #changedFiles = self.hgclient.getModifiedFiles()
        changedFiles = changedFiles["added"] + changedFiles["nottracked"]
        return self._mercurialLinesToPackageTuples(changedFiles)

    def getJPackageTuplesWithModifiedMetadata(self):
        hg = self.bitbucketclient.getMercurialClient(self.bitbucketreponame)
        changedFiles = hg.getModifiedFiles()
        
        #changedFiles = self.hgclient.getModifiedFiles()
        changedFiles = changedFiles["modified"]
        return self._mercurialLinesToPackageTuples(changedFiles)

    def getJPackageTuplesWithDeletedMetadata(self):
        hg = self.bitbucketclient.getMercurialClient(self.bitbucketreponame)
        changedFiles = hg.getModifiedFiles()      
        
        #changedFiles = self.hgclient.getModifiedFiles()
        changedFiles = changedFiles["removed"] + changedFiles['missing']
        return self._mercurialLinesToPackageTuples(changedFiles)

    # Packages that have been deleted will never have modified files
    def getJPackageTuplesWithModifiedFiles(self):
        # Add packages with modified files
        changedJPackages=set()
        for jpackages in self.getJPackages():
            if jpackages.hasModifiedFiles():
                changedJPackages.add((jpackages.domain, jpackages.name, jpackages.version))
        return list(changedJPackages)

    def getModifiedJPackages(self):
        """reloadconfig
        Returns a list with all the packages whose files or metadata have been changed in the currently active domain
        """      
        if self.metadataFromTgz:
            raise RuntimeError("Cannot use modified jpackages from tgz metdata repo")
        changedFiles = self.mercurialclient.getModifiedFiles()
        changedFiles=changedFiles["removed"] + changedFiles['missing']+changedFiles["modified"]+changedFiles["added"] + changedFiles["nottracked"]
        modpackages= self._mercurialLinesToPackageTuples(changedFiles)
        modpackages.extend(self.getJPackageTuplesWithModifiedFiles())
        return modpackages

    def hasDomainChanged(self):
        return self.hasModifiedMetadata() or self.hasModifiedFiles()

    def publishMetadata(self, commitMessage='',force=False): # tars are not uploadable
        """
        Publishes all metadata of the currently active domain
        """
        j.logger.log("Publish metadata for domain %s" % self.domainname,2)
        if not self.metadataFromTgz:
            hg = self.bitbucketclient.getMercurialClient(self.bitbucketreponame)
            hg.commit(message=commitMessage,force=force)
            hg.push()
        else:
            raise RuntimeError('Meta data is comming from tar for domain ' + self.domainname + ', cannot publish modified metadata.')


    def publish(self, commitMessage):
        """
        Publishes the currently active domain's bundles & metadata
        
        @debug: It is recommended to NOT use publish() 
                Use a combination of updateMetadata(), publishMetadata() and upload() instead.
                Reason publish() changes the build numbers on top of update()
        """
        if 'JSBASE' in os.environ:
            raise RuntimeError("No publishing allowed in sandboxed mode")        
        j.logger.log("Publish metadata for jpackages domain: %s " % self.domainname ,2)

        # determine which packages changed
        modifiedPackages, mess = self.showChangedItems()
        
        if j.application.shellconfig.interactive:
            if not j.console.askYesNo('continue?'):
                return

        j.logger.log('publishing packages:\n' + mess, 5)

        if not commitMessage:
            commitMessage = j.console.askString('please enter a commit message')

        j.logger.log("1) Updating buildNumbers in metadata and uploading files", 1)
        deletedPackagesMetaData = self.getJPackageTuplesWithDeletedMetadata()
        modifiedPackagesMetaData = self.getJPackageTuplesWithModifiedMetadata()
        modifiedPackagesFiles = self.getJPackageTuplesWithModifiedFiles()
        for jpackagesActive in modifiedPackages:
            if jpackagesActive in deletedPackagesMetaData:
                j.logger.log("Deleting files of package " + str(jpackagesActive), 1)
                j.system.fs.removeDirTree(j.packages.getDataPath(*jpackagesActive))
            else:
            #if jpackagesActive in newPackagesMetaData or jpackagesActive in modifiedPackagesMetaData:
                jpackagesActiveObject = j.packages.get(jpackagesActive[0], jpackagesActive[1], jpackagesActive[2])
                j.logger.log("For jpackages: " + str(jpackagesActiveObject), 1)
                j.logger.log("current numbers : " + jpackagesActiveObject.reportNumbers(), 1)
                # Update build number
                jpackagesActiveObject.buildNr  = jpackagesActiveObject.buildNr + 1

                # Update meta and bundle number
                if jpackagesActive in modifiedPackagesMetaData:
                    jpackagesActiveObject.metaNr = jpackagesActiveObject.buildNr
                if jpackagesActive in modifiedPackagesFiles:
                    jpackagesActiveObject.bundleNr = jpackagesActiveObject.buildNr
                j.logger.log("updated to new numbers : " + jpackagesActiveObject.reportNumbers(), 1)
                jpackagesActiveObject.save()

            # At this point we may be
            if jpackagesActive in modifiedPackagesFiles:
                jpackagesActiveObject = j.packages.get(jpackagesActive[0], jpackagesActive[1], jpackagesActive[2])
                #jpackagesActiveObject._compress(overwriteIfExists=True)
                jpackagesActiveObject.upload()
        

        j.logger.log("2) Commiting and uploadind metadata with updated buildNumbers", 1)
        self.updateMetadata(commitMessage=commitMessage)  #makes sure metadata from tmp & active repo is updated
        self.publishMetadata(commitMessage=commitMessage)

        # Only do this after complete success!
        # If something goes wrong we know which files where modified
        for jpackagesActive in modifiedPackagesFiles:
            jpackagesActiveObject = j.packages.get(jpackagesActive[0], jpackagesActive[1], jpackagesActive[2])
            jpackagesActiveObject._resetPreparedForUpdatingFiles()
    
    
    def showChangedItems(self):    
        """
        Shows all changes in the files or metadata
        """
        j.logger.log("Show changes in files and metadata for jpackages domain: %s " % self.domainname ,2)

        # determine which packages changed
        newPackagesMetaData      = self.getJPackageTuplesWithNewMetadata()
        modifiedPackagesMetaData = self.getJPackageTuplesWithModifiedMetadata() + newPackagesMetaData
        deletedPackagesMetaData  = self.getJPackageTuplesWithDeletedMetadata()
        modifiedPackagesFiles    = self.getJPackageTuplesWithModifiedFiles()
        modifiedPackages         = list(set(newPackagesMetaData + modifiedPackagesMetaData + deletedPackagesMetaData + modifiedPackagesFiles))

        # If there are no packages to do something with don't bother the user
        # with annoying questions
        if not modifiedPackages:
            j.logger.log("There where no modified packages for domain: %s " % self.domainname , 1)
            return modifiedPackages, ''  #debug

        # report to the user what will happen if he proceeds
        j.logger.log('The following packages will be published:', 1)
        just = 15
        mess  = ' ' * 4 + 'domain:'.ljust(just) + 'name:'.ljust(just) + 'version:'.ljust(just)
        mess +=           'metachanged:'.ljust(just) + 'fileschanged:'.ljust(just) + 'status:'.ljust(just) + '\n'
        for package in modifiedPackages:
            metachanged  = package in modifiedPackagesMetaData
            fileschanged = package in modifiedPackagesFiles

            status = 'UNKOWN-ERROR'
            if package in newPackagesMetaData:
                status = 'NEW'
            elif package in modifiedPackagesMetaData:
                status = 'MODIFIED'
            elif package in deletedPackagesMetaData:
                status = 'DELETED'
            elif package in modifiedPackagesFiles:
                status = 'FILES MODIFIED'
            else:
                raise RuntimeError('Unkown status!')

            mess += ' ' * 4 + package[0].ljust(just) + package[1].ljust(just) + package[2].ljust(just)
            mess +=           str(metachanged).ljust(just) + str(fileschanged).ljust(just) + str(status).ljust(just) + '\n'

        j.logger.log('publishing packages for domain %s:\n' % self.domainname + mess, 1)
                    
        return modifiedPackages, mess
    
    def linkMetadata(self):
        sourcepath = self.getMetadataDir()
        destpath=j.system.fs.joinPaths(j.dirs.packageDir,"metadata",self.domainname)
        j.system.fs.createDir(sourcepath)            
        j.system.fs.symlink(sourcepath,destpath,True)

    def updateMetadata(self, commitMessage="",force=False, accessCode=''):
        """
        Get all metadata of the currently active domain's repo servers and store locally
        
        Depends on the parameter metadataFromTgz.
        Note: Changing the configuration of metadataFromTgz will usually erase 
        the local uncommited modifications of the metadata.
        
        @debug: It is recommended to NOT use publish() 
                Use a combination of updateMetadata(), publishMetadata() and upload() instead.
                Reason publish() changes the build numbers on top of update()
        """
        
        if self.metadataFromTgz == False:

            j.action.start("Update JPackages metadata for domain %s" % self.domainname,\
                           "Could not update the metadata for the domain",\
                           "go to directory %s and update the metadata yourself using mercurial" % self.metadatadir)
                  
            #self.bitbucketclient.checkoutMerge    
            self.vcsclient.update()
       
            #link code to right metadata location
            sourcepath = self.getMetadataDir()
            destpath=j.system.fs.joinPaths(j.dirs.packageDir,"metadata",self.domainname)
            j.system.fs.createDir(sourcepath)            
            j.system.fs.symlink(sourcepath,destpath,True)
            
            j.action.stop()
        else:
            repoUrl        = self.metadataDownload
            targetTarDir   = j.packages.getMetaTarPath(self.domainname)
            targetTarFileName = ("metadata_jp"+'_'+self.domainname+'_'+self.qualitylevel+'.tgz')
            remoteTarPath  = j.system.fs.joinPaths(repoUrl, targetTarFileName)  #@todo P3 needs to work with new tar filenames corresponding to qualitylevels
 
            j.logger.log("Getting meta data from a tar: %s" % remoteTarPath, 1)
            
            if not j.system.fs.exists(targetTarDir):
                j.system.fs.createDir(targetTarDir)
            j.cloud.system.fs.copyFile(remoteTarPath, 'file://' +  targetTarDir) # Add protocol

            ## Extract the tar to the correct location
            if j.system.fs.exists(self.metadatadir):
                j.system.fs.removeDirTree(self.metadatadir)
            targetTarPath = j.system.fs.joinPaths(targetTarDir, targetTarFileName)
            
            j.system.fs.targzUncompress(targetTarPath, self.metadatadir)
            #Note: Syslinks were just overwritten
            
        # Reload all packages
        for package in self.getJPackages():
            package.load()

    def mergeMetadata(self, commitMessage=""):
        """
        #@todo doc
        """
        self._ensureInitialized()
        if not self.metadataFromTgz:
            j.action.start("update & merge jpackages metadata for domain %s" % self.domainname,\
                           "Could not update/merge the metadata for the domain",\
                           "go to directory %s and update/merge/commit the metadata yourself using mercurial" % self.metadatadir)
            hgclient=self.bitbucketclient.getMercurialClient(self.bitbucketreponame)            
            hgclient.pull()
            hgclient.updatemerge(commitMessage=commitMessage,ignorechanges=False,addRemoveUntrackedFiles=True,trymerge=True)	    
            #self.hgclientTmp.pullupdate(commitMessage=commitMessage) ? not needed no?
            j.action.stop()
        else:
            raise RuntimeError("Cannot merge metadata from tgz info, make sure in sources.cfg file this domain %s metadata is not coming from a tgz file"% self.domainname)

        # Reload all packages
        for package in self.getJPackages():
            package.reload()	    

    def publishMetaDataAsTarGz(self):
        
        #self._ensureInitialized()
        revisionTxt = j.system.fs.joinPaths(self.metadatadir, 'revision.txt')
        
        if self.metadataFromTgz == False:
            hg = self.bitbucketclient.getMercurialClient(self.bitbucketreponame)
            id = hg.id()            
            j.system.fs.writeFile(revisionTxt, id) #this to remember from which revision the tgz has been created
            
        targetTarDir  = j.packages.getMetaTarPath(self.domainname)
        targetTarFileName = ("metadata_jp"+'_'+self.domainname+'_'+self.qualitylevel+'.tgz')
        targetTarPath = j.system.fs.joinPaths(targetTarDir, targetTarFileName)
        
        j.logger.log("Building tar file from " + self.metadatadir + " to location " + targetTarPath)

        j.system.fs.targzCompress(self.metadatadir, targetTarPath, pathRegexExcludes=['.*\/\.hg\/.*'])
        
        j.system.fs.remove(revisionTxt)    
        
        remoteTarDir  = self.metadataUpload
        j.logger.log("Uploading tar file for jpackages metadata" + targetTarPath + " to location " + remoteTarDir)
        j.cloud.system.fs.copyFile('file://' +  targetTarPath, 'file://' +  remoteTarDir + "/")        
        j.system.fs.remove(targetTarPath)
    

    def _isTrackingFile(self, file):
        # test if the file is commited
        file.replace(self.metadatadir,"")
        if file[0]=="/":
            file=file[1:]
        curpath=j.system.fs.getcwd()
        j.system.fs.changeDir(self.metadatadir)
        hgclient=self.bitbucketclient.getMercurialClient(self.bitbucketreponame)
        result=hgclient.isTrackingFile(file)
        j.system.fs.changeDir(curpath)
        return result

    def getLatestBuildNrForJPackage(self,domain,name,version):
        """
        Returns the lastest buildnumber
        Buildnr comes from default tip of mercurial repo
        """        
        jpackages=j.packages.get(domain,name,version,"default",fromTmp=True)
        return jpackages.buildNr

    def getJPackages(self):
        """
        Returns a list of all jpackages of the currently active domain
        """
        return j.packages._find(domain=self.domainname)
    
    def removeDebugStateFromAll(self):
        for package in self.getJPackages():
            package.removeDebugModeInJpackage()
    
    def switchQualityLevel(self, qlevel):
        '''
        Allows a clean reconfiguration for a new quality level, and be sure that the configurations are OK.
        All packages are reinstalled, if need.
        NO active removal of unneeded packages.
        Includes a check that the repository has the new quality level
        '''
        if 'JSBASE' in os.environ:
            raise RuntimeError("No switchQualityLevel in sandboxed mode")                  
        j.console.echo("\nDomain:  %s\n %s (Repo)\n %s (Quality Level)\n %s (MetaFromTgz)\n" % (self.domainname,self.bitbucketreponame,self.qualitylevel,self.metadataFromTgz))
        self.updateMetadata()
        
        #check that new quality level is valid in this metadata repo
        list=[]
        list = j.system.fs.listDirsInDir(path=self._sourcepath, dirNameOnly=True)
        if qlevel in list:
            j.console.echo("Found matching Quality Level in repo. - %s - has quality level: %s" % (self.domainname, qlevel))
        else:
            raise RuntimeError("Metadata repo %s of domain %s has no such Quality Level %s " % (self.bitbucketreponame, self.domainname, qlevel))
        
        self._ensureInitialized()
        QLFrom = self.qualitylevel
        
        self.qualitylevel = qlevel
        self.saveConfig()
        
        self._ensureInitialized()
        QLTo = self.qualitylevel
        j.console.echo("Changed quality level of domain %s from: %s to: %s " % (self.domainname,QLFrom, QLTo))
        
        #reinstall all packages of domain, if needed       
        for package in self.getJPackages():
            package.reload()
            j.console.echo("%s %s" % (package.name, package.version))
            
            #find at least one platform with a checksum
            matchOne = False
            for platform in package.supportedPlatforms:
                c = package.getChecksum(platform)
                if c != None:
                    j.console.echo("    %s %s " % (platform, c))
                    matchOne = True
            
            if matchOne == True:
                package.install(dependencies=False, reinstall=True, download=True)
                j.console.echo("\n    >>>> Successful Download")
            else: 
                j.console.echo("    No checksum for any platform of this package/version.")
        
        self.updateMetadata()  #importantly, this resets the symlink to the metadata directories
                
        return 0
        
    def __str__(self):
        self._ensureInitialized()
        return "domain:%s\nmetadataDownload:%s\nmetadataUpload:%s\nqualitylevel:%s\nmetadataFromTgz:%s\n" % \
               (self.domainname,self.metadataDownload,self.metadataUpload,self.qualitylevel,self.metadataFromTgz)

    def __repr__(self):
        return self.__str__()

    def _ensureDomainCanBeUpdated(self):
        if self.metadataFromTgz:
            raise RuntimeError('For domain: ' + self.domainname + ': Meta data comes from tgz, cannot update domain.')
        if self.metadataUpload == None:
            raise RuntimeError('For domain: ' + self.domainname + ': Not metadataUpload location specified, cannot update domain.')
