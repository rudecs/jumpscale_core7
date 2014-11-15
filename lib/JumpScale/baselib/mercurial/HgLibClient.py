'''Utility methods to work with hg repositories'''
from JumpScale import j
import sys
sys.path.append(j.system.fs.joinPaths(j.dirs.jsLibDir,"baselib","mercurial"))
import hglib
import JumpScale.baselib.codetools
import os
import hashlib
        
class HgLibClient:    

    # _configs = ['ui.merge=internal:merge']  @todo is this ok to remove? (kds)
    _configs = []


    def __init__(self, hgbasedir, remoteUrl="", branchname=None, cleandir=None):
        """
        @param base dir where local hgrepository will be stored
        @param remote url of hg repository, can be empty if local repo is created
        @branchname "" means is the tip, None means will try to fetch the branchname from the basedir
        @param cleandir: If True, files in that directory will be deleted before doing clone (if it wasn't an mercurial) if set to False,
                         an exception will be raised if directory has files, if None, the user will be asked interactively.
        """
        self.remoteUrl = remoteUrl.strip()
        self.basedir = hgbasedir
        self.branchname = branchname
        if not self.branchname:
            self.branchname = 'default'

        if remoteUrl<>"":
            self._log("mercurial remoteurl:%s"%(remoteUrl),category="config")
        
        if (not isinstance(hgbasedir, basestring) or not isinstance(remoteUrl, basestring))\
         or (branchname and not isinstance(branchname, basestring)):
            raise ValueError("Input to hgclient need to be all strings")

        if not self.isInitialized() and not self.remoteUrl:
            raise RuntimeError(".hg not found and remote url is not supplied")


        if j.system.fs.exists(self.basedir) and not self.isInitialized():
            if len(j.system.fs.listFilesInDir(self.basedir,recursive=True))==0:
                self._clone()
            else:
                #did not find the mercurial dir
                if j.application.interactive:
                    if cleandir == None and self.remoteUrl<>"":
                        cleandir = j.gui.dialog.askYesNo("\nDid find a directory but there was no mercurial metadata inside.\n\tdir: %s\n\turl:%s\n\tIs it ok to remove all files from the target destination before cloning the repository?"\
                                                       % (self.basedir,self.remoteUrl))
                        
                if cleandir:
                    j.system.fs.removeDirTree(self.basedir)
                    j.system.fs.createDir(self.basedir)
                    self._clone()
                else:
                    self._raise("Could not clone %s to %s, target dir was not empty" % (self.basedir,self.remoteUrl))
            
        elif not j.system.fs.exists(self.basedir):
            j.system.fs.createDir(self.basedir)
            self._clone()
        else:
            self.client = hglib.open(self.basedir, configs=self._configs)
            self.remoteUrl = self.getUrl()
            currentbranchname = self.getbranchname()
            if branchname and branchname != currentbranchname:
                self.switchbranch(branchname)
                currentbranchname = branchname
            self.branchname = currentbranchname

            
        self.reponame, self.repokey = self._getRepoNameAndKey()

    def _getRepoNameAndKey(self):
        path = self.basedir

        def getNameAndKeyFromPath(p):
            name = os.path.basename(p.rstrip(os.path.sep))
            unique = hashlib.sha1(p).hexdigest()
            return name, "%s_%s" % (name, unique)

        if path.startswith(j.dirs.codeDir):
            subPath = path[len(j.dirs.codeDir):].strip(os.path.sep)
            parts = subPath.split(os.path.sep)
            if len(parts) != 2:
                return getNameAndKeyFromPath(path)

            user, name = parts
            return name, "%s_%s" % (user, name)
        else:
            return getNameAndKeyFromPath(path)
       
    def isInitialized(self):
        return j.system.fs.exists(j.system.fs.joinPaths(self.basedir,".hg"))

    def patchHgIgnore(self):
        #create or update the hgignore file
        hgignore="""
.pyc$
.swp$
~$
.project
.pydevproject
_generatedcode/*
.metadata
syntax: regexp
.project
\._.*
/_remote/
.orig$
"""
        ignorefilepath = j.system.fs.joinPaths(self.basedir,".hgignore")
        if j.system.fs.exists(self.basedir) and not j.system.fs.exists(ignorefilepath):
            j.system.fs.writeFile(ignorefilepath,hgignore)
            
        elif  j.system.fs.exists(self.basedir):
            #add items not in hgignore yet
            lines=hgignore.split("\n")
            inn=j.system.fs.fileGetContents(ignorefilepath)
            linesExisting=inn.split("\n")
            linesout=[]
            for line in linesExisting:
                if line.strip()<>"":
                    linesout.append(line)
            for line in lines:
                if line not in linesExisting and line.strip()<>"":
                    linesout.append(line)
            out="\n".join(linesout)
            if out.strip()<>inn.strip():
                j.system.fs.writeFile(ignorefilepath,out)

    def isConnected(self): #??
        try:
            self.client.outgoing()
        except:
            return False
        return True
    
    def verify(self, die=True):
        errors = list()
        def eh(exitcode, stdout, stderr):
            if exitcode != 0:
                errors.append(stderr)
        command = hglib.util.cmdbuilder('verify')
        self.client.rawcommand(command, eh=eh)
        if errors and die:
            self._raise("invalid repo, output verify: <<<<<<<<<<<<<<<<<<<<\n" + errors[0] + "\n>>>>>>>>>>>>>>>>>>")
        return not bool(errors)


    def verifyfix(self):
        """
        verify repo and try to fix
        @return True if fixed
        """
        self._log("mercurial verify %s" % (self.basedir),2)
        if not self.verify(False):
            msg="Mercurial directory on %s is corrupt." % (self.basedir)
            if j.application.interactive:
                j.console.echo(msg)
                if j.gui.dialog.askYesNo("/nDo you want to repair the situation by removing the corrupt directory and clone again?"):
                    j.system.fs.removeDirTree(self.basedir)
                    self.__init__(self.basedir,self.remoteUrl)                  
                    return True
            else:
                self._raise("Mercurial directory on %s is corrupt." % (self.basedir))
        self.isConnected()
        self._log("Verified repo on %s, no issues found" % self.basedir)
        return False

    
    def _log(self, message, level=5,category=""):
        message="repo:%s  %s" % (self.basedir,message)
        j.clients.mercurial.log(message,category,level)

    def _raise(self, message):        
        message="ERROR hgclient: %s\nPlease fix the merurial local repo manually and restart failed mercurial action.\nRepo is %s" % (message, self.basedir)
        raise RuntimeError(message)
    
    def pull(self):
        self._log("pull %s to %s" % (self.remoteUrl,self.basedir))
        self.client.pull(source=self.remoteUrl)
    
    def isTrackingFile(self, file):
        self._log("isTrackingFile of %s" % (self.basedir))
        status = self.client.status()
        for item in status:
            if item[1] == file and item[0] == '?':
                return False
        return True

    def getModifiedFiles(self):
        """
        return array with changed files in repo
        @return {"added":added,"missing":missing,"modified":modified,"ignored":ignored,"removed":removed,"nottracked":nottracked} is dict
        remarks
        - missing means, file referenced in mercurial local repo but no longer on filesystem (! in hg status) 
        - notracked mans, file is on filesystem but not in repo (?)
        - removed means, mercurial repo knows file has been removed from filesystem (R)
        - ignored, means hg has been instructed to ignore that file (I)
        """
        #@todo rewrite using self.client
        self._log("getChangedFiles of %s" % (self.basedir))
        
        # first remove backup files as these confuse the system
        # If the system contains backup files raise an exception
        files  = j.system.fs.listFilesInDir(self.basedir, recursive=True)
        for file in files:
            if file[-1] == '~': # if backupfile
                j.system.fs.remove(file)
        self._removeRedundantFiles()
        rules = self.status()
        modified=[]
        added=[]
        ignored=[]
        removed=[]
        missing=[]
        nottracked=[]
        for rule in rules:
            code = rule[0]
            path = rule[1]
            if code == "!":
                missing.append(path)
            elif code == "I":
                ignored.append(path)
            elif code == "?":
                nottracked.append(path)
            elif code == "M":
                modified.append(path)
            elif code == "A":
                added.append(path)
            elif code == "R":
                removed.append(path)      
        return {"added":added,"missing":missing,"modified":modified,"ignored":ignored,"removed":removed,"nottracked":nottracked}
    
    def hasModifiedFiles(self):
        r = self.getModifiedFiles()
        if any(r.values()):
            return True
        else:
            return False            
            
    def updatemerge(self, commitMessage="", addRemoveUntrackedFiles=True, pull=False, user=None,force=False):
        self._log("updatemerge %s" % (self.basedir))
        self.checkbranch()
        if pull:
            self.pull()
        updateresult=self.update(die=False)
        if addRemoveUntrackedFiles:
            self.addRemoveInteractive(commitMessage,user,force)
        self.commitInteractive(commitMessage,user,force)
        result = self.merge(commit=False)
        if result == 1 or result == 2:
            # j.console.log("There was nothing to merge")
            pass
        else:
            print "MERGE DONE: WILL COMMIT NOW."
            self.commitInteractive(commitMessage,user,force)
        updateresult=self.update(die=False)
        if updateresult==False:
            raise RuntimeError("BUG:update should not fail at this point, because all addedremoved, merged & committed.")
        if self.hasModifiedFiles():
            raise RuntimeError("BUG: there should be no uncommitted files at this point")
            
    def addRemoveInteractive(self,commitMessage="", user=None,force=False):

        result= self.getModifiedFiles()

        def remove(items):
            for item in items:
                path=j.system.fs.joinPaths(self.basedir,item)
                if j.system.fs.exists(path):
                    if j.system.fs.isDir(path):
                        j.system.fs.removeDir(path)
                    else:
                        j.system.fs.remove(path)

        remove(result["ignored"])

        addremove=False

        #means files not added to repo
        if len(result["nottracked"])>0:
            if force==False and j.application.interactive:
                j.console.echo("\n\nFound files not added yet to repo.")
                j.console.echo("\n".join(["To Add: %s" % item for item in result["nottracked"]]))
                add=j.gui.dialog.askYesNo("Above files are not added yet to repo but on filesystem, is it ok to add these files (No will remove)?")
                if add==False:
                    j.console.echo("remove the nontracked files.\n\n")
                    j.console.echo("\n".join(["Will Remove: %s" % item for item in result["nottracked"]]))
                    sure=j.gui.dialog.askYesNo("are you sure you want to remove above mentioned files.")
                    if sure:
                        remove(result["nottracked"])
                    else:
                        j.console.echo("Please manually add your files and restart operation.")
                        j.application.stop()                        
                else:
                    addremove=True
            elif force:
                addremove=True
            else:
                raise RuntimeError("Cannot addremove, did not force operation.")

        #means files are in repo but no longer on filesystem
        if len(result["missing"])>0:
            if force==False and j.application.interactive:
                j.console.echo("\n\nFound files in repo which are no longer on filesystem, so probably deleted.")
                j.console.echo("\n".join(["To remove from repo: %s" % item for item in result["missing"]]))
                remove=j.gui.dialog.askYesNo("Above files are in repo but no longer on filesystem, is it ok to delete these files from repo?")
                if remove==False:
                    j.console.echo("Please manually get your missing files back and restart operation.")
                    j.application.stop()
            elif force:
                addremove=True                
            else:
                raise RuntimeError("Cannot addremove, did not force operation.")
            
        self.addremove() #does not commit yet

        self.commitInteractive(commitMessage,user=user,force=force)

    def commitInteractive(self,commitMessage="",user=None,force=False):
            
        result=self.getModifiedFiles()   
        if any([result["added"], result["removed"], result["modified"]]):
            if j.application.interactive:
                j.console.echo("\nFound modified, added, deleted files not committed yet")
                j.console.echo("\n".join(["Added:    %s" % item for item in result["added"]]))
                j.console.echo("\n".join(["Removed:  %s" % item for item in result["removed"]]))
                j.console.echo("\n".join(["Modified: %s" % item for item in result["modified"]]))                    
                if force or j.gui.dialog.askYesNo("\nDo you want to commit the files?"):
                    commitMessage=self.commit(commitMessage, user=user)
                elif j.gui.dialog.askYesNo("\nDo you want to ignore the changed files? The changes will be lost"):
                    self.update(force=True)
                else:
                    self._raise("Cannot update repo because uncommitted files in %s" % self.basedir)        
            else:
                if force:
                    self.commit(commitMessage, user=user)
                else:
                    self._raise("Cannot update repo because uncommitted files in %s" % self.basedir)


    def update(self, die=True, force=False, rev=None):
        self._log("update %s " % (self.basedir))
        try:
            self.client.update(rev=rev, clean=force)
        except:
            if die:
                raise
            return False
        return True
         
    def remove(self, *paths):
        """
        remove file(s) with path from local repo
        """
        mypaths = list()
        for val in paths:
            mypaths.append(j.system.fs.joinPaths(self.basedir, val))
        self._log("remove file from local repo with path %s" % mypaths,8)
        self.client.remove(mypaths)

    def merge(self, commitMessage="", commit=True, user=None):
        self._log("merge '%s'" % (self.basedir))
        self.checkbranch()
        # self._removeRedundantFiles()
        if self.hasModifiedFiles():
            self._raise("Cannot merge %s because there are untracked files." % self.basedir)

        heads=[item for item in  self.client.heads() if item.branch==self.branchname]
        if len(heads)==1:
            #no need to merge
            return 1
        elif len(heads)==0:
            raise RuntimeError("BUG: there should always be at least 1 head with the expected branchname:%s"%self.branchname)
        else:
            #need merge
            try:
                self.client.merge()
                returncode = 0
                out = ''
            except hglib.client.error.CommandError, e:
                self._log("merge %s" % e)
                out = e.err
                returncode = e.ret

            if out.find("nothing to merge")<>-1 or out.find("has one head")<>-1 :
                self._log("Nothing to merge",5)
                return 1
            if out.find("conflicts during merge")<>-1:
                self._raise("conflicts in merge")
            
            if returncode > 0:
                self._raise("cannot merge, cmd was hg merge in dir %s" % self.basedir)            

            if commit:
                self.commit(commitMessage, force=True, user=user)
            return 0
                    
    def switchbranch(self,branchname):
        self._log("switchbranch %s" % (self.basedir))
        if branchname != self.getbranchname():
            self.update(rev=branchname)
        
    def pullupdate(self, force=False):
        self._log("pullupdate %s" % (self.basedir),category="pullupdate")
        self.pull()    
        self.update(force=force)

    def _clone(self):
        self._log("clone %s" % (self.basedir),category="clone")
        self.client = hglib.clone(self.remoteUrl, self.basedir, branch=self.branchname, configs=self._configs)
        self.pull()
        self.verify()

    def getbranchname(self):
        return self.client.branch()

    def checkbranch(self):
        """
        check if branch of client is consistent with branch found on local repo
        will raise error if not ok
        """
        if self.branchname:
            if self.getbranchname() != self.branchname:
                force=False
                if j.application.interactive:
                    if j.gui.dialog.askYesNo("\nBranchnames conflict for repo, jshell mercurial client has branchname: %s and branchname on filesystem: %s\nThis might result in loosing code changes. \nDo you want to continue, this will pull & update to the branch?" % (self.branchname,self.getbranchname())):
                        self.pullupdate(force=True)
                if not force:
                    self._raise("Branchnames conflict for repo, jshell mercurial client has branchname: %s and branchname on filesystem: %s" % (self.branchname,self.getbranchname()))

                
    def getbranches(self):
        return [ b[0] for b in self.client.branches()]

    def getbranchmap(self):
        branches = self.client.branches()
        return {x[0]: x[2] for x in branches}
        
    def isPushNeeded(self):
        return bool(self.client.outgoing())
    
    def status(self):
        return self.client.status()
    
    def id(self):
        return self.client.identify(id=True).strip()
        
    identify = id

    def incoming(self, source="default"):
        path = self.getConfigItem('paths', source)
        if not path:
            self._raise("Invalid source %s" % source)
        return self.client.incoming(path=path)

    def commit(self, message="", addremove=True, checkStatus=True, force=False,
            user=None):
        """
        commit changes to local repo
        """
        self._log("commit %s" % (self.basedir))

        if not user:
            self._assertCommitterInfo()

        self.checkbranch()

        if not self.status():
            self._log("Nothing to commit, e.g. after a merge which had nothing to do.",5)
            return 
        if j.application.interactive and not message:
            message = j.gui.dialog.askString("give commit message:")
        elif not message:
            raise RuntimeError("need commit message")

        self._log("commit %s" % (self.basedir))
        self.client.commit(message, addremove=addremove, user=user)
        return message

    def addremove(self, message=None):
        """
        addremove files and commit if commit message is given
        """
        self._log("addremove '%s'" % (self.basedir))
        self.checkbranch()   
        if not self.status():
            self._log("Nothing to addremove",2)
            return 
        self._removeRedundantFiles()
        self.client.addremove()
        if message:
            self.commit(message)        
        
    def push(self,branch=None,newbranch=False):
        self._log("push %s to %s" % (self.basedir, self.remoteUrl))
        url = self.getUrl()
        if branch<>None:
            if newbranch:
                self.client.push(dest=url,newbranch=newbranch)
            else:
                self.client.push(dest=url,branch=branch)
        else:
            self.client.push(dest=url,newbranch=newbranch)
        
    def commitpush(self, commitMessage="", ignorechanges=False,
            addRemoveUntrackedFiles=False, trymerge=True, pull=True, user=None):
        """
        reponame is name under which we are going checkout in dir targetdir, if not specified same as name repository
        """
        self._log("commitpush %s" % (self.basedir))
        if pull:
            self.pull()        
        try:
            self.updatemerge(commitMessage, ignorechanges,
                    addRemoveUntrackedFiles, trymerge, pull=False, user=user)
            self.push()        
        except:
            j.logger.exception("Failed to update/merge/push %s" % self)
            self.pull()  #now try to pull first
            self.updatemerge(commitMessage, ignorechanges,
                    addRemoveUntrackedFiles, trymerge, pull=False, user=user)
            self.push()        

    def _removeRedundantFiles(self):
        self._log("removeredundantfiles %s" % (self.basedir))
        dirs2delete=[]
        def process(args, path):
            if path[-4:].lower()==".pyc" or path[-4:].lower()==".pyo" or path[-4:].lower()==".pyw" or path[-1]=="~":
                j.system.fs.remove(path)
            if path.find("/.cache")<>-1 and path.find("/.hg/")==-1:
                dirs2delete.append(path)
        j.system.fswalker.walk(self.basedir,process,"",True,True) 
        for cachedir in dirs2delete:
            j.system.fs.removeDirTree(cachedir)

    def getConfigItem(self, section, key):
        config = self.client.config(section)
        for item in config:
            if item[1] == key:
                return item[2]

    def getUrl(self):
        if self.remoteUrl:
            return self.remoteUrl
        else:
            return self.getConfigItem('paths', 'default')
        
    def log(self, fromdaysago=0, fromdate=0, fromkey=None):
        """
        @fromdate needs to be in epoch
        """
        if fromdaysago<>0:
            datecmd=fromdaysago
        elif fromdate<>0:
            datecmd=fromdate        
        else:
            datecmd=""
           
        return self.client.log(date=datecmd, revrange=fromkey)


    def getFileChangeNodes(self, path, fromNode="-1", toNode="0", limit=None):
        """
        Get the commit hash of all commits that changed `path`.

        @param path: path to look for, relative to the repository root
        @type path: string
        @param fromNode: start looking from this revision onwards, default: latest
        @type fromNode: string
        @param toNode: stop looking at this revision, default: first
        @type toNode: string
        @param limit: maximum amount of changes to return
        @type limit: int
        @return: commit hash of all commits that changed `path`
        @rtype: list(string)
        """
        revrange = "%s:%s" % (fromNode, toNode)
        path = j.system.fs.joinPaths(self.basedir, path)
        logs = self.client.log(files=[path], revrange=revrange)
        return [ log.node for log in logs ]

    def cat(self, rev, path):
        """
        Return the content of the file at `path` in commit `rev`

        @param rev: commit identifier
        @type rev: string
        @param path: path of the file to cat, relative to the repository root
        @type path: string
        @return: content of the file at `path` in commit `rev`
        @rtype: string
        """
        path = j.system.fs.joinPaths(self.basedir, path)
        return self.client.cat([path], rev=rev)

    def walk(self, rev, paths, callback):
        """
        Walk over the files in `rev` that match the argument `paths`, and call
        `callback` with the repository instance and the file context as
        arguments.

        @param rev: ID of the revision to walk in
        @type rev: string
        @param paths: glob-style path list
        @type paths: list(string)
        @param callback: will be called for each match
        @type callback: callable
        """
        changectx = self.client[rev]
        fullPaths = [ os.path.join(self.basedir, p) for p in paths]
        matcher = changectx.match(pats=fullPaths)
        walker = changectx.walk(matcher)
        for matchedPath in walker:
            filectx = changectx.filectx(matchedPath)
            callback(self._repo, filectx)

    def _assertCommitterInfo(self):
        """
        Make sure relevant committer information is included in commit messages.
        """
        user = self.getConfigItem('ui', 'username')
        if user:
            return

        hgrclocation = j.system.fs.joinPaths(os.environ["HOME"], ".hgrc")
        if j.system.fs.exists(hgrclocation):
            raise RuntimeError("A hgrc file exists at %s, but no username was "
                    "filled in in the [ui] section" % hgrclocation)
        else:
            name = j.gui.dialog.askString("\n\nSpecify your username & email address for mercurial\n e.g Firstname Lastname <firstname.lastname@example.net>\n")
            config = "[ui]\nusername = %s\nverbose = True\n" % name
            j.system.fs.writeFile(hgrclocation, config)
            self.reset()

    def reset(self):
        """
        Reset this client.

        Mercurial saves some state linked to the repo object. If a hg pull
        happened, the repo object seems unable to notice the pulled commits. So
        in this method, we replace the repo object with a new one.
        """
        try:
            self.client.close()
        except:
            pass
        self.client = hglib.open(self.basedir)

    def close(self):
        try:
            self.client.close()
        except:
            pass


    def __del__(self):
        self.close()

    def __str__(self):
        msg="%s %s %s" % (self.remoteUrl, self.basedir, self.branchname)
        return msg
    
    __repr__ = __str__ 
    
