from JumpScale import j
import JumpScale.baselib.gitlab
import JumpScale.baselib.blobstor2
import os

from .JSFileMgr import JSFileMgr

class BackupClient:
    """
    """

    def __init__(self,backupname,blobstorAccount,blobstorNamespace,gitlabAccount,compress=True,fullcheck=False,servercheck=True,storpath="/mnt/STOR"):
     
        self.backupname=backupname
        self.blobstorAccount=blobstorAccount
        self.blobstorNamespace=blobstorNamespace
        self.gitlabAccount=gitlabAccount
        self.key="backup_%s"%self.backupname

        j.logger.disable()
        

        # try:
        #     self.gitlab=j.clients.gitlab.get(gitlabAccount)
        # except Exception,e:
        #     self.gitlab=None

        self.mdpath="/opt/backup/MD/%s"%self.backupname
        if not j.system.fs.exists(path=self.mdpath):  
            # #init repo
            # if self.gitlab.passwd<>"":              
            #     if not self.gitlab.existsProject(namespace=self.gitlab.loginName, name=self.key):
            #         self.gitlab.createproject(self.key, description='backup set', \
            #         issues_enabled=0, wall_enabled=0, merge_requests_enabled=0, wiki_enabled=0, snippets_enabled=0, public=0)#, group=accountname)   
            #     from IPython import embed
            #     print "DEBUG NOW id"
            #     embed()
                    
            #     url = 'git@%s:%s/%s.git' % (self.gitlab.addr,gitlabAccount,self.key)
            #     j.system.fs.createDir(self.mdpath)
            #     def do(cmd):
            #         cmd="cd %s;%s"%(self.mdpath,cmd)
            #         print cmd
            #         j.system.process.executeWithoutPipe(cmd)    
            #     do("git init")                
            #     do("touch README")
            #     do("git add README")
            #     do("git commit -m 'first commit'")
            #     do("git remote add origin %s"%url)
            #     do("git push -u origin master")
            # else:
            #     from IPython import embed
            #     print "DEBUG NOW id"
            #     embed()
                
            j.system.fs.createDir(self.mdpath)
       

        
        # if self.gitlab<>None:
        #     self.gitclient = self.gitlab.getGitClient(self.gitlab.loginName, self.key, clean=False,path=self.mdpath)
        # else:
        #     self.gitclient=None

        self.fullcheck=fullcheck
        self.servercheck=servercheck
            
        self.filemanager=JSFileMgr(MDPath=self.mdpath,backupname=self.backupname,blobstorAccount=blobstorAccount,\
                blobstorNamespace=blobstorNamespace,compress=compress,fullcheck=fullcheck,servercheck=servercheck)


    def backup(self,path,destination="", pathRegexIncludes={},pathRegexExcludes={},childrenRegexExcludes=[".*/dev/.*","/proc/.*"]):
        # self._clean()
        return self.filemanager.backup(path,destination=destination, pathRegexIncludes=pathRegexIncludes,pathRegexExcludes=pathRegexExcludes,\
            childrenRegexExcludes=childrenRegexExcludes)
        # self.commitMD()

    def getMDFromBlobStor(self,key):
        """
        get metadata from blobstor
        """
        self.filemanager.blobstorMD.downloadDir(key,dest=self.filemanager.MDPath,repoid=self.filemanager.repoid,compress=True)


    def sendMDToBlobStor(self):
        return self.filemanager.sendMDToBlobStor()

    def restore(self,src,destination,link=False):
        # self.pullMD()
        self.filemanager.restore(src=src,dest=destination,link=link)


    def _clean(self):
        for ddir in j.system.fs.listDirsInDir(self.mdpath,False,True,findDirectorySymlinks=False):
            if ddir.lower()!=".git":
                j.system.fs.removeDirTree(j.system.fs.joinPaths(self.mdpath,ddir))
        for ffile in j.system.fs.listFilesInDir(self.mdpath, recursive=False, followSymlinks=False):
            j.system.fs.remove(ffile)
        

    # def backupRecipe(self,recipe):
    #     """
    #     do backup of sources as specified in recipe
    #     example recipe

    #     #when star will do for each dir
    #     /tmp/JSAPPS/apps : * : /DEST/apps
    #     #when no * then dir & below
    #     /tmp/JSAPPS/bin :  : /DEST/bin
    #     #now only for 1 subdir
    #     /tmp/JSAPPS/apps : asubdirOfApps : /DEST/apps

    #     """
    #     self._clean()
    #     self.filemanager.backupRecipe(recipe)
    #     self.commitMD()

    def commitMD(self):
        print("commit to git")
        self.gitclient.commit("backup %s"%j.base.time.getLocalTimeHRForFilesystem())
        if j.system.net.tcpPortConnectionTest(self.gitlab.addr,self.gitlab.port):
            #found gitlab
            print("push to git")
            self.gitclient.push(force=True)
        else:
            print("WARNING COULD NOT COMMIT CHANGES TO GITLAB, no connection found.\nDO THIS LATER!!!!!!!!!!!!!!!!!!!!!!")

    def pullMD(self):
        print("pull from git")        
        if j.system.net.tcpPortConnectionTest(self.gitlab.addr,self.gitlab.port):
            #found gitlab
            self.gitclient.pull()        
        else:
            print("WARNING COULD NOT PULL CHANGES FROM GITLAB, no connection found.\nDO THIS LATER!!!!!!!!!!!!!!!!!!!!!!")
