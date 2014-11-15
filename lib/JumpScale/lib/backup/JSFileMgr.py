from JumpScale import j
import JumpScale.baselib.gitlab
import os

class Item():
    def __init__(self,data=""):
        state="start"
        self.hash=""
        self.text=""
        self.size=0
        self.mtime=0

        if data<>"":
            for line in data.split("\n"):
                if line.strip()=="" or line[0]=="#":
                    continue
                if line.find("####")<>-1:
                    state="text"
                    continue
                if state=="start":
                    key,value=line.split(":")
                    self.__dict__[key.strip()]=value.strip()
                if state=="text":
                    self.text+="%s\n"%line

    def __repr__(self):
        out=""
        for key,value in self.__dict__.iteritems():
            if key<>"text":
                out+="%s:%s\n"%(key,value)
        out+="####\n"
        out+=self.text
        return out

    __str__=__repr__

from .BlobStorClientFake import BlobStorClientFake

class JSFileMgr():
    def __init__(self, MDPath,backupname,blobstorAccount,blobstorNamespace,repoid=0,compress=True,fullcheck=False,servercheck=True,storpath="/mnt/STOR"):
        self.errors=[]
        self._MB4=1024*1024*4 #4Mbyte
        self.excludes=["*.pyc"]
        self.repoid=repoid

        self.servercheck=servercheck
        self.fullcheck=fullcheck

        self.MDPath = MDPath

        self.storpath = storpath  # Intermediate link path!
        j.system.fs.createDir(self.storpath)

        passwd = j.application.config.get('grid.master.superadminpasswd')
        login="root"
        # blobstor2 client
        # self.blobstor = j.servers.zdaemon.getZDaemonClient("127.0.0.1",port=2345,user=login,passwd=passwd,ssl=False,sendformat='m', returnformat='m',category="blobserver")
        if blobstorAccount==None:
            self.blobstor=BlobStorClientFake()
            self.blobstorMD=BlobStorClientFake()
        else:
            self.blobstor=j.clients.blobstor2.getClient(name=blobstorAccount,domain="backups",namespace=blobstorNamespace)
            self.blobstorMD=j.clients.blobstor2.getClient(name=blobstorAccount,domain="backups",namespace="md_%s"%blobstorNamespace)

        self.blobstor.cachepath="/mnt/BLOBCACHEC"
        j.system.fs.createDir(self.blobstor.cachepath)        
        
        self.namespace=blobstorNamespace
        self.backupname=backupname

        self.blobstor.compress=compress
        self.blobstorMD.compress=compress
        self.errors=[]

        self.blobstorMD.cachepath=""

        self.link=False

        self.restorebatch=[]
        self.restorebatchSize=0

    def _normalize(self, path):
        path=path.replace("'","\\'")
        path=path.replace("[","\\[")
        path=path.replace("]","\\]")
        return path

    def doError(self,path,msg):
        self.errors.append([path,msg])

    def _handleMetadata(self, path,destination,prefix,ttype,linkdest=None):
        """
        @return (mdchange,contentchange) True if changed, False if not
        @param destination is destination inside target dir 
        """
        # print "MD:%s "%path,

        srcpart=j.system.fs.pathRemoveDirPart(path,prefix,True)                        
        dest=j.system.fs.joinPaths(self.MDPath,"MD",destination,srcpart)
        dest2=j.system.fs.joinPaths(destination,srcpart)
        dest2=dest2.lstrip("/")
        change=False

        try:
            stat=os.lstat(path)
        except Exception,e:
            if not j.system.fs.exists(path):
                #can be link which does not exist
                #or can be file which is deleted in mean time
                self.doError(path,"could not find, so could not backup.") 
                return (False,False,"",dest2)

        #next goes for all types
        if j.system.fs.exists(path=dest):
            if ttype=="D":
                dest+="/.meta"
            item=self.getMDObjectFromFs(dest)            
            mdchange=False
        elif ttype=="L":
            dest=j.system.fs.joinPaths(self.MDPath,"LINKS",destination,srcpart)
            if j.system.fs.exists(path=dest):
                if j.system.fs.exists(j.system.fs.joinPaths(dest,".meta")):
                    #is dir
                    dest=j.system.fs.joinPaths(dest,".meta")
                item=self.getMDObjectFromFs(dest)
                mdchange=False
            else:
                item=Item()
                mdchange=True
        else:
            item=Item()
            mdchange=True

        if ttype=="F":          
            sizeFromFS=int(stat.st_size)
            if self.fullcheck or item.mtime<>str(int(stat.st_mtime)) or item.size<>str(sizeFromFS):
                if sizeFromFS<>0:
                    newMD5=j.tools.hash.md5(path)
                    if item.hash<>newMD5:                        
                        change=True
                        item.hash=newMD5
                mdchange=True
        elif ttype=="L":
            if not item.__dict__.has_key("dest"):
                mdchange=True          
            elif linkdest<>item.dest:
                mdchange=True

        if mdchange==False:
            #check metadata changed based on mode, uid, gid & mtime
            if ttype=="F":
                if int(item.size)<>int(stat.st_size):
                    mdchange==True
            if int(item.mtime)<>int(stat.st_mtime) or int(item.mode)<>int(stat.st_mode) or\
                    int(item.uid)<>int(stat.st_uid) or int(item.gid)<>int(stat.st_gid):
                mdchange=True                

        if mdchange:
            print "MD:%s CHANGE"%path

            # print "MDCHANGE"
            item.mode=int(stat.st_mode)
            item.uid=int(stat.st_uid)
            item.gid=int(stat.st_gid)
            # item.atime=stat.st_atime
            item.ctime=int(stat.st_ctime)
            item.mtime=int(stat.st_mtime)

            if ttype=="F":
                item.size=stat.st_size
                item.type="F"
                j.system.fs.createDir(j.system.fs.getDirName(dest))
            elif ttype=="D":
                item.type="D"
                dest=j.system.fs.joinPaths(self.MDPath,"MD",destination,srcpart,".meta")
                j.system.fs.createDir(j.system.fs.getDirName(dest))
            elif ttype=="L":                
                item.dest=linkdest
                if j.system.fs.isDir(path):
                    dest=j.system.fs.joinPaths(self.MDPath,"LINKS",destination,srcpart,".meta")
                    item.type="LD"
                else:
                    dest=j.system.fs.joinPaths(self.MDPath,"LINKS",destination,srcpart)
                    item.type="LF"
                j.system.fs.createDir(j.system.fs.getDirName(dest))

            j.system.fs.writeFile(dest, str(item))

        return (mdchange,change,item.hash,dest2)

    def restore(self, src,dest,link=False):
        """
        dest is where to restore to
        """

        j.system.fs.removeDirTree(dest)
        self.errors=[]

        # if src[0] == "/":
        #     raise RuntimeError("not supported src path")
    
        #DIRS & FILES
        src2 = "%s/%s/%s" % (self.MDPath, "MD",src)

        if not j.system.fs.exists(path=src2):
            raise RuntimeError("Could not find MD source '%s'"%src2)

        #restore dirs
        for item in j.system.fs.listFilesInDir(src2, True,filter=".meta"):
            mdo=self.getMDObjectFromFs(item)
            destpart=j.system.fs.pathRemoveDirPart(item, src2, True)
            destfull=j.system.fs.joinPaths(dest, destpart)
            destfull=j.system.fs.getDirName(destfull)
            self.restore1dir(item, destfull)

        #restore files
        for item in j.system.fs.listFilesInDir(src2, True):
            if j.system.fs.getBaseName(item)==".meta":
                continue
            destpart=j.system.fs.pathRemoveDirPart(item, src2, True)
            destfull=j.system.fs.joinPaths(dest, destpart)

            self.restore1file(item, destfull,link=link,sync=False)

        print "done downloading files, make sure we have the last batch."
        self.blobstor.downloadBatch() #this will make sure we get last batch

        #LINKS
        src2 = "%s/%s" % (self.MDPath, "LINKS")

        if j.system.fs.exists(path=src2):
            for item in j.system.fs.listFilesInDir(src2, True,filter=".meta"):
                mdo=self.getMDObjectFromFs(item)
                destpart=j.system.fs.pathRemoveDirPart(item, src2, True)
                destfull=j.system.fs.joinPaths(dest, destpart)
                destfull=j.system.fs.getDirName(destfull)
                destlink=j.system.fs.joinPaths(dest, mdo.dest)
                # print "link %s to %s"%(destfull,destlink)
                j.system.fs.symlink( destlink, destfull, overwriteTarget=True)
                #os.chmod(destfull,int(mdo.mode))
                #os.chown(destfull,int(mdo.uid),int(mdo.gid))                         

            for item in j.system.fs.listFilesInDir(src2, True):
                if j.system.fs.getBaseName(item)==".meta":
                    continue
                mdo=self.getMDObjectFromFs(item)
                destpart=j.system.fs.pathRemoveDirPart(item, src2, True)
                destfull=j.system.fs.joinPaths(dest, destpart)
                destlink=j.system.fs.joinPaths(dest, mdo.dest)
                # print "link %s to %s"%(destfull,destlink)
                j.system.fs.symlink( destlink, destfull, overwriteTarget=True)
                #os.chmod(destfull,int(mdo.mode))
                #os.chown(destfull,int(mdo.uid),int(mdo.gid))   

    def getMDObjectFromFs(self,path):
        itemObj=Item(j.system.fs.fileGetContents(path))
        return itemObj

    def restore1file(self, src, dest,sync=True,link=False):
        """
        """

        print "restore file: %s" % (dest)

        if j.system.fs.getBaseName(src).find("__dev")==0:
            #restore device files
            itemObj=self.getMDObjectFromFs(src)
            dest2=j.system.fs.getTmpFilePath()+".tgz"
            self.blobstor.downloadFile(key=itemObj.hash,dest=dest2,link=False,repoid=self.repoid,chmod=0,chownuid=0,chowngid=0,sync=True)
            destDev=j.system.fs.getDirName(dest)
            cmd="cd %s;tar xzvf %s -C ."%(destDev,dest2)
            j.system.process.execute(cmd)
            j.system.fs.remove(dest2)            
        else:
            itemObj=self.getMDObjectFromFs(src)
            j.system.fs.createDir(j.system.fs.getDirName(dest))

            if itemObj.hash.strip()=="":
                j.system.fs.writeFile(dest,"")
                os.chmod(dest, int(itemObj.mode))
                os.chown(dest, int(itemObj.uid), int(itemObj.gid))
                return
            self.blobstor.downloadFile(key=itemObj.hash,dest=dest,link=link,repoid=self.repoid,chmod=int(itemObj.mode),chownuid=int(itemObj.uid),chowngid=int(itemObj.gid)\
               ,sync=sync,size=itemObj.size)      

    def restore1dir(self,src,dest):
        print "restore dir: %s %s" % (src, dest)

        itemObj=self.getMDObjectFromFs(src)
        j.system.fs.createDir(dest)
        # chmod/chown
        os.chmod(dest,int(itemObj.mode))
        os.chown(dest,int(itemObj.uid),int(itemObj.gid))        

    def backupBatch(self,batch,batchnr=None,total=None):
        """
        batch is [[src,md5]]
        """

        key2paths={}            
        for src,md5 in batch:
            if md5<>"":
                key2paths[md5]=(src,md5)

        print "batch nr:%s check"%batchnr
        exists=self.blobstor.existsBatch(keys=key2paths.keys()) 

        nr=batchnr*1000 #for print purposes, so we see which file is uploading

        for src,md5 in batch:
            if md5=="":
                continue
            nr+=1
            if not md5 in exists:
                self.blobstor.uploadFile(src,key=md5,repoid=self.repoid)

        self.blobstor.sync() #to make sure all is send because batching is being used
        print "uploaded batch:%s %s/%s"%(batchnr,nr,total)

    def backup(self,path,destination="", pathRegexIncludes={},pathRegexExcludes={"F":"*\\.pyc"},childrenRegexExcludes=[".*/dev/.*",".*/proc/.*"]):

        #check if there is a dev dir, if so will do a special tar
        ##BACKUP:
        #tar Szcvf testDev.tgz saucy-amd64-base/rootfs/dev/
        ##restore
        #tar xzvf testDev.tgz -C testd
        self._createExistsList(destination)

        #DEAL WITH DEV dirs
        print "SCAN for dev dirs"
        # for ddir in j.system.fs.listDirsInDir( path=path, recursive=True, dirNameOnly=False, findDirectorySymlinks=False):
        w=j.base.fswalker.get()
        callbackMatchFunctions=w.getCallBackMatchFunctions(pathRegexIncludes={},pathRegexExcludes={},includeFolders=True,includeLinks=False)

        def processdir(path,stat,arg):
            if j.system.fs.getDirName(path+"/", lastOnly=True, levelsUp=0)=="dev":
                pathdev=j.system.fs.getDirName(path)
                cmd="cd %s;tar Szcvf __dev.tgz dev"%pathdev
                j.system.process.execute(cmd)

        callbackFunctions={}
        callbackFunctions["D"]=processdir
        arg={}
        w.walk(path,callbackFunctions,arg=arg,callbackMatchFunctions=callbackMatchFunctions,childrenRegexExcludes=childrenRegexExcludes)

        print "SCAN MD:%s"%path
        
        self.errors=[]

        destMDClist=j.system.fs.joinPaths(self.storpath, "../TMP","plists",self.namespace,destination,".mdchanges")
        destFClist=j.system.fs.joinPaths(self.storpath, "../TMP","plists",self.namespace,destination,".fchanges")
        destFlist=j.system.fs.joinPaths(self.storpath, "../TMP","plists",self.namespace,destination,".found")
        j.system.fs.createDir(j.system.fs.getDirName(destMDClist))
        j.system.fs.createDir(j.system.fs.getDirName(destFClist))
        j.system.fs.createDir(j.system.fs.getDirName(destFlist))
        mdchanges = open(destMDClist, 'w')
        changes = open(destFClist, 'w')
        found = open(destFlist, 'w')

        w=j.base.fswalker.get()
        callbackMatchFunctions=w.getCallBackMatchFunctions(pathRegexIncludes,pathRegexExcludes,includeFolders=True,includeLinks=True)

        def processfile(path,stat,arg):
            if path[-4:]==".pyc":
                return
            self=arg["self"]
            prefix=arg["prefix"]
            mdchange,fchange,md5,path2=self._handleMetadata(path,arg["destination"],prefix=prefix,ttype="F")
            if mdchange:
                arg["mdchanges"].write("%s\n"%(path2))
            if self.servercheck or fchange:
                arg["changes"].write("%s|%s\n"%(path,md5))
            arg["found"].write("%s\n"%path2)

        def processdir(path,stat,arg):
            self=arg["self"]
            prefix=arg["prefix"]
            mdchange,fchange,md5,path=self._handleMetadata(path,arg["destination"],prefix=prefix,ttype="D")
            if mdchange:
                arg["mdchanges"].write("%s\n"%path)
            arg["found"].write("%s\n"%path)            

        def processlink(src,dest,stat,arg):
            # print "LINK: %s %s"%(src,dest)
            path=src
            self=arg["self"]
            prefix=arg["prefix"]
            destpart=j.system.fs.pathRemoveDirPart(dest,prefix,True)                                   
            mdchange,fchange,md5,path=self._handleMetadata(path,arg["destination"],prefix=prefix,ttype="L",linkdest=destpart)
            if mdchange:
                arg["mdchanges"].write("%s\n"%path)
            arg["found"].write("%s\n"%path)            

        callbackFunctions={}
        callbackFunctions["F"]=processfile
        callbackFunctions["D"]=processdir
        callbackFunctions["L"]=processlink            

        arg={}
        arg["self"]=self
        arg["prefix"]=path
        arg["changes"]=changes
        arg["mdchanges"]=mdchanges
        arg["found"]=found
        arg["destination"]=destination

        # arg["batch"]=[]
        w.walk(path,callbackFunctions,arg=arg,callbackMatchFunctions=callbackMatchFunctions,childrenRegexExcludes=childrenRegexExcludes)

        changes.close()
        found.close()
        mdchanges.close()
        
        # self.backupBatch(arg["batch"])

        if len(self.errors)>0:
            out=""
            for path0,msg in self.errors:
                out+="%s:%s\n"%(path0,msg)
            epath=j.system.fs.joinPaths(self.MDPath,"ERRORS",destination,"ERRORS.LOG")
            j.system.fs.createDir(j.system.fs.getDirName(epath))
            j.system.fs.writeFile(epath,out)

        #now we need to find the deleted files
        #sort all found files when going over fs
        cmd="sort %s | uniq > %s_"%(destFlist,destFlist)
        j.system.process.execute(cmd)
        originalFiles=j.system.fs.joinPaths(self.storpath, "../TMP","plists",self.namespace,destination,".mdfound")
        cmd="sort %s | uniq > %s_"%(originalFiles,originalFiles)
        j.system.process.execute(cmd)
        deleted=j.system.fs.joinPaths(self.storpath, "../TMP","plists",self.namespace,destination,".deleted")
        #now find the diffs
        cmd="diff %s_ %s_ -C 0 | grep ^'- ' > %s"%(originalFiles,destFlist,deleted)
        rcode,result=j.system.process.execute(cmd,False)
        # if not(rcode==1 and result.strip().replace("***ERROR***","")==""):
        #     raise RuntimeError("Could not diff : cmd:%s error: %s"%(cmd,result))

        #DEAL WITH DELETED FILES
        f=open(deleted, "r")
        for line in f:
            line=line.strip()
            path0=line.lstrip("- ")
            dest=j.system.fs.joinPaths(self.MDPath,"MD",path0)
            j.system.fs.removeDirTree(dest)
            dest=j.system.fs.joinPaths(self.MDPath,"LINKS",path0)
            j.system.fs.removeDirTree(dest)
        f.close()
        print "SCAN DONE MD:%s"%path

        print "START UPLOAD FILES."
        #count lines
        total=0
        f=open(destFClist, "r")
        for line in f:
            total+=1
        f.close()
        print "count done"
        f=open(destFClist, "r")
        counter=0
        batch=[]
        batchnr=0
        for line in f:
            path0,md5=line.strip().split("|")
            batch.append([path0,md5])
            counter+=1
            if counter>1000:                
                self.backupBatch(batch,batchnr=batchnr,total=total)
                batch=[]
                counter=0
                batchnr+=1
        #final batch
        if batch<>[]:
            self.backupBatch(batch,batchnr=batchnr,total=total)
        f.close()

        self.blobstor.sync()

        key=self.sendMDToBlobStor()

        print "BACKUP DONE."

        return key

    def sendMDToBlobStor(self):
        key=self.blobstorMD.uploadDir(self.MDPath,compress=True)
        self.blobstorMD.sync()
        return key

    def _createExistsList(self,dest):
        # j.system.fs.pathRemoveDirPart(dest,prefix,True)
        print "Walk over MD, to create files which we already have found."
        destF=j.system.fs.joinPaths(self.storpath, "../TMP","plists",self.namespace,dest,".mdfound")
        j.system.fs.createDir(j.system.fs.getDirName(destF))
        fileF = open(destF, 'w')

        def processfile(path,stat,arg):
            path2=j.system.fs.pathRemoveDirPart(path, arg["base"], True)
            path2=path2.lstrip("/")
            if path2[0:2]=="MD":
                path2=path2[3:]
            if path2[0:5]=="LINKS":
                path2=path2[6:]
            path2=path2.lstrip("/")
            # print path2
            if path2[-5:]==".meta":
                return
            # print "%s  :   %s"%(path,path2)
            # if j.system.fs.isDir(path2):
            #     path=j.system.fs.joinPaths(path,".meta")
            # md=self.getMDObjectFromFs(path)
            # fileF.write("%s|%s|%s|%s\n"%(path2,md.size,md.mtime,md.hash))
            fileF.write("%s\n"%(path2))

        callbackFunctions={}
        callbackFunctions["F"]=processfile
        callbackFunctions["D"]=processfile

        arg={}
        arg["base"]=self.MDPath
        w=j.base.fswalker.get()
        callbackFunctions["F"]=processfile

        wpath=j.system.fs.joinPaths(self.MDPath,"MD",dest)
        if j.system.fs.exists(path=wpath):
            w.walk(wpath,callbackFunctions=callbackFunctions,arg=arg,childrenRegexExcludes=[])
        wpath=j.system.fs.joinPaths(self.MDPath,"LINKS",dest)
        if j.system.fs.exists(path=wpath):
            w.walk(wpath,callbackFunctions=callbackFunctions,arg=arg,childrenRegexExcludes=[])

        fileF.close()
        print "Walk over MD, DONE"


    # def linkRecipe(self, src, dest):
    #     """
    #     Hardlink Recipe from Cache Dir
    #     """

    #     if not self.storpath:
    #         raise RuntimeError("Link Path is not Set!")

    #     if src[0] != "/":
    #         src = "%s/%s" % (self.MDPath, src.strip())

    #     if not j.system.fs.exists(path=src):
    #         raise RuntimeError("Could not find source (on mdstore)")

    #     for item in j.system.fs.listFilesInDir(src, True):
    #         # Retrieve blob & blob_path in intermediate location
    #         blob_path = self._restoreBlob(item, namespace)

    #         # the hardlink destination
    #         destpart = j.system.fs.pathRemoveDirPart(item, src, True)
    #         destfull = j.system.fs.joinPaths(dest, destpart)

    #         # Now, make the link
    #         self._link(blob_path, destfull)

