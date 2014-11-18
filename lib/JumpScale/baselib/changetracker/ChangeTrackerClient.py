from JumpScale import j
import lzma
import JumpScale.baselib.gitlab



class ChangeTrackerClient():
    def __init__(self, MDPath,namespace="backup"):
        self.errors=[]

        self.excludes=["*.pyc"]

        self.MDPath = MDPath

        if cachePath=="":
            cachePath="/opt/backup/CACHE"

        self.cachePath = cachePath  # Intermediate link path!

        # Local blob STOR
        self.STORpath="/opt/backup/STOR"

        passwd = j.application.config.get('grid.master.superadminpasswd')
        login="root"
        # blobstor2 client
        # self.client = j.servers.zdaemon.getZDaemonClient("127.0.0.1",port=2345,user=login,passwd=passwd,ssl=False,sendformat='m', returnformat='m',category="blobserver")
        self.client=j.clients.blobstor2.getClient(namespace=namespace, name=blobclientname)
        self.namespace=namespace
        self.repoId=1 # will be implemented later with osis
        self.compress=False
        self.errors=[]

    def _normalize(self, path):
        path=path.replace("'","\\'")
        path=path.replace("[","\\[")
        path=path.replace("]","\\]")
        return path

    def action_link(self, src, dest):
        #DO NOT IMPLEMENT YET
        j.system.fs.createDir(j.system.fs.getDirName(dest))
        print("link:%s %s"%(src, dest))

        if j.system.fs.exists(path=dest):
            stat=j.system.fs.statPath(dest)
            if stat.st_nlink<2:
                raise RuntimeError("only support linked files")
        else:
            cmd="ln '%s' '%s'"%(self._normalize(src),self._normalize(dest))
            try:
                j.system.process.execute(cmd)
            except Exception as e:
                print("ERROR")
                print(cmd)
                print(e)
                self.errors.append(["link",cmd,e])

    def _dump2stor(self, data,key=""):
        if len(data)==0:
            return ""
        if key=="":
            key = j.tools.hash.md5_string(data)
        data2 = lzma.compress(data) if self.compress else data
        if not self.client.exists(key=key,repoId=self.repoId):
            self.client.set(key=key, data=data2,repoId=self.repoId)
            
        return key

    def _read_file(self,path, block_size=0):
        if block_size==0:
            block_size=self._MB4

        with open(path, 'rb') as f:
            while True:
                piece = f.read(block_size)
                if piece:
                    yield piece
                else:
                    return

    def doError(self,path,msg):
        self.errors.append([path,msg])

    def _handleMetadata(self, path,destination,prefix,ttype,linkdest=None,fullcheck=False):
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
            stat=j.system.fs.statPath(path)
        except Exception as e:
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
            if fullcheck or item.mtime!=stat.st_mtime or item.size!=stat.st_size:
                newMD5=j.tools.hash.md5(path)
                if item.hash!=newMD5:
                    mdchange=True
                    change=True
                    item.hash=newMD5
        elif ttype=="L":
            if "dest" not in item.__dict__:
                mdchange=True          
            elif linkdest!=item.dest:
                mdchange=True

        if mdchange==False:
            #check metadata changed based on mode, uid, gid & mtime
            if ttype=="F":
                if int(item.size)!=int(stat.st_size):
                    mdchange==True
            if int(item.mtime)!=int(stat.st_mtime) or int(item.mode)!=int(stat.st_mode) or\
                    int(item.uid)!=int(stat.st_uid) or int(item.gid)!=int(stat.st_gid):
                mdchange=True                

        if mdchange:
            print("MD:%s CHANGE"%path)

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

    def restore(self, src, dest, namespace):
        """
        src is location on metadata dir
        dest is where to restore to
        """
        self.errors=[]

        if src[0] != "/":
            src = "%s/%s" % (self.MDPath, src.strip())

        if not j.system.fs.exists(path=src):
            raise RuntimeError("Could not find source (on mdstore)")

        for item in j.system.fs.listFilesInDir(src, True):
            destpart=j.system.fs.pathRemoveDirPart(item, src, True)
            destfull=j.system.fs.joinPaths(dest, destpart)

            self.restore1file(item, destfull, namespace)

    def getMDObjectFromFs(self,path):
        itemObj=Item(j.system.fs.fileGetContents(path))
        return itemObj

    def restore1file(self, src, dest, namespace):

        print("restore: %s %s" % (src, dest))

        itemObj=self.getMDObjectFromFs(src)

        j.system.fs.createDir(j.system.fs.getDirName(dest))

        if itemObj.hash.strip()=="":
            j.system.fs.writeFile(dest,"")
            return

        blob_path = self._getBlobPath(namespace, itemObj.hash)
        if j.system.fs.exists(blob_path):
            # Blob exists in cache, we can get it from there!
            print("Blob FOUND in cache: %s" % blob_path)
            j.system.fs.copyFile(blob_path, dest)
            return

        # Get the file directly or get the blob storing the hashes of file parts!
        blob_hash = itemObj.hashlist if hasattr(itemObj, "hashlist") else itemObj.hash

        # Get blob from blobstor2
        blob = self.client.get(namespace, blob_hash)

        # Write the blob
        self._writeBlob(dest, blob, itemObj, namespace)

    def _writeBlob(self, dest, blob, item, namespace):
        """
        Write blob to destination
        """

        check="##HASHLIST##"
        if blob.find(check)==0:
            # found hashlist
            print("FOUND HASHLIST %s" % blob)
            hashlist = blob[len(check) + 1:]
            j.system.fs.writeFile(dest,"")
            for hashitem in hashlist.split("\n"):
                if hashitem.strip() != "":
                    blob_block = self.client.get(namespace, hashitem)
                    data = lzma.decompress(blob_block)
                    j.system.fs.writeFile(dest, data, append=True)
        else:
            # content is there
            data = lzma.decompress(blob)
            j.system.fs.writeFile(dest, data)

        # chmod/chown
        os.chmod(dest,int(item.mode))
        os.chown(dest,int(item.uid),int(item.gid))

    def backupBatch(self,batch,batchnr=None,total=None):
        """
        batch is [[src,md5]]
        """
        key2paths={}            
        for src,md5 in batch:
            key2paths[md5]=(src,md5)

        print("batch nr:%s check"%batchnr)
        notexist=self.client.existsBatch(keys=list(key2paths.keys())) 
        print("batch checked on unique data")

        nr=batchnr*1000

        for src,md5 in batch:
            nr+=1
            if md5 in notexist:
                hashes=[]
                if j.system.fs.statPath(src).st_size>self._MB4:
                    print("%s/%s:upload file (>4MB) %s"%(nr,total,src))
                    for data in self._read_file(src):
                        hashes.append(self._dump2stor(data))
                    if len(hashes)>1:
                        out = "##HASHLIST##\n"
                        hashparts = "\n".join(hashes)
                        out += hashparts
                        # Store in blobstor
                        out_hash = self._dump2stor(out,key=md5) #hashlist is stored on md5 location of file
                    else:
                        raise RuntimeError("hashist needs to be more than 1.")
                else:
                    print("%s/%s:upload file (<4MB) %s"%(nr,total,src))
                    for data in self._read_file(src):
                        hashes.append(self._dump2stor(data,key=md5))
            else:
                print("%s/%s:no need to upload, exists: %s"%(nr,total,src))

    def backup(self,path,destination="", pathRegexIncludes={},pathRegexExcludes={".*\\.pyc"},childrenRegexExcludes=[".*/dev/.*",".*/proc/.*"],fullcheck=False):

        #check if there is a dev dir, if so will do a special tar
        ##BACKUP:
        #tar Szcvf testDev.tgz saucy-amd64-base/rootfs/dev/
        ##restore
        #tar xzvf testDev.tgz -C testd
        self._createExistsList(destination)

        print("SCAN MD:%s"%path)
        
        self.errors=[]

        if j.system.fs.exists(j.system.fs.joinPaths(path,"dev")):
            cmd="cd %s;tar Szcvf __dev.tgz dev"%path
            j.system.process.execute(cmd)

        destMDClist=j.system.fs.joinPaths(self.STORpath, "../TMP","plists",self.namespace,destination,".mdchanges")
        destFClist=j.system.fs.joinPaths(self.STORpath, "../TMP","plists",self.namespace,destination,".fchanges")
        destFlist=j.system.fs.joinPaths(self.STORpath, "../TMP","plists",self.namespace,destination,".found")
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
            mdchange,fchange,md5,path2=self._handleMetadata(path,arg["destination"],prefix=prefix,ttype="F",fullcheck=arg["fullcheck"])
            if mdchange:
                arg["mdchanges"].write("%s\n"%(path2))
            if arg["fullcheck"] or fchange:
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
        arg["fullcheck"]=fullcheck

        # arg["batch"]=[]
        w.walk(path,callbackFunctions,arg=arg,callbackMatchFunctions=callbackMatchFunctions,childrenRegexExcludes=childrenRegexExcludes)

        changes.close()
        found.close()
        mdchanges.close()
        
        # self.backupBatch(arg["batch"])

        if len(self.errors)>0:
            out=""
            for path,msg in self.errors:
                out+="%s:%s\n"%(path,msg)
            epath=j.system.fs.joinPaths(self.MDPath,"ERRORS",destination,"ERRORS.LOG")
            j.system.fs.createDir(j.system.fs.getDirName(epath))
            j.system.fs.writeFile(epath,out)

        #now we need to find the deleted files
        #sort all found files when going over fs
        cmd="sort %s | uniq > %s_"%(destFlist,destFlist)
        j.system.process.execute(cmd)
        originalFiles=j.system.fs.joinPaths(self.STORpath, "../TMP","plists",self.namespace,destination,".mdfound")
        cmd="sort %s | uniq > %s_"%(originalFiles,originalFiles)
        j.system.process.execute(cmd)
        deleted=j.system.fs.joinPaths(self.STORpath, "../TMP","plists",self.namespace,destination,".deleted")
        #now find the diffs
        cmd="diff %s_ %s_ -C 0 | grep ^'- ' > %s"%(originalFiles,destFlist,deleted)
        rcode,result=j.system.process.execute(cmd,False)
        # if not(rcode==1 and result.strip().replace("***ERROR***","")==""):
        #     raise RuntimeError("Could not diff : cmd:%s error: %s"%(cmd,result))

        f=open(deleted, "r")
        for line in f:
            line=line.strip()
            path=line.lstrip("- ")
            dest=j.system.fs.joinPaths(self.MDPath,"MD",path)
            j.system.fs.removeDirTree(dest)
            dest=j.system.fs.joinPaths(self.MDPath,"LINKS",path)
            j.system.fs.removeDirTree(dest)
        f.close()
        print("SCAN DONE MD:%s"%path)

        print("START UPLOAD FILES.")
        #count lines
        total=0
        f=open(destFClist, "r")
        for line in f:
            total+=1
        f.close()
        print("count done")
        f=open(destFClist, "r")
        counter=0
        batch=[]
        batchnr=0
        for line in f:
            path,md5=line.strip().split("|")
            batch.append([path,md5])
            counter+=1
            if counter>1000:                
                self.backupBatch(batch,batchnr=batchnr,total=total)
                batchnr+=1
        #final batch
        self.backupBatch(batch,batchnr=batchnr,total=total)
        f.close()
        print("BACKUP DONE.")

    def _createExistsList(self,dest):
        # j.system.fs.pathRemoveDirPart(dest,prefix,True)
        print("Walk over MD, to create files which we already have found.")
        destF=j.system.fs.joinPaths(self.STORpath, "../TMP","plists",self.namespace,dest,".mdfound")
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
        print("Walk over MD, DONE")

    def _getBlobPath(self, namespace, key):
        """
        Get the blob path in Cache dir
        """
        # Get the Intermediate path of a certain blob
        storpath = j.system.fs.joinPaths(self.cachePath, namespace, key[0:2], key[2:4], key)
        return storpath

    def _getBlob(self, src, namespace):
        """
        Retrieves the blobs in Cache path
        """

        # Create the Item Object
        itemObj = Item(j.system.fs.fileGetContents(src))

        blob_hash = itemObj.hashlist if hasattr(itemObj, "hashlist") else itemObj.hash

        # Get blob from blobstor2
        blob = self.client.get(key=blob_hash)

        # The path which this blob should be saved
        blob_path = self._getBlobPath(namespace, itemObj.hash)
        j.system.fs.createDir(j.system.fs.getDirName(blob_path))

        self._writeBlob(blob_path, blob, itemObj, namespace)

        return blob_path

    def linkRecipe(self, src, dest, namespace):
        """
        Hardlink Recipe from Cache Dir
        """

        if not self.cachePath:
            raise RuntimeError("Link Path is not Set!")

        if src[0] != "/":
            src = "%s/%s" % (self.MDPath, src.strip())

        if not j.system.fs.exists(path=src):
            raise RuntimeError("Could not find source (on mdstore)")

        for item in j.system.fs.listFilesInDir(src, True):
            # Retrieve blob & blob_path in intermediate location
            blob_path = self._getBlob(item, namespace)

            # the hardlink destination
            destpart = j.system.fs.pathRemoveDirPart(item, src, True)
            destfull = j.system.fs.joinPaths(dest, destpart)

            # Now, make the link
            self.action_link(blob_path, destfull)

class BackupClient:
    """
    """

    def __init__(self,backupname,blobclientName,gitlabName="incubaid"):
        self.blobclientName=blobclientName
        self.gitlabName=gitlabName        
        self.gitlab=j.clients.gitlab.get(gitlabName)
        self.backupname=backupname
        self.mdpath="/opt/backup/MD/%s"%backupname
        if not j.system.fs.exists(path=self.mdpath):    
            if not self.gitlab.existsProject(namespace=self.gitlab.loginName, name=backupname):
                self.gitlab.createproject(backupname, description='backup set', issues_enabled=0, wall_enabled=0, merge_requests_enabled=0, wiki_enabled=0, snippets_enabled=0, public=0)#, group=accountname)            
        self.gitclient = self.gitlab.getGitClient(self.gitlab.loginName, backupname, clean=False,path=self.mdpath)
            
        self.filemanager=JSFileMgr(MDPath=self.mdpath,namespace="backup",blobclientname=blobclientName)

    def backup(self,path,destination="", pathRegexIncludes={},pathRegexExcludes={},childrenRegexExcludes=[".*/dev/.*","/proc/.*"],fullcheck=False):
        # self._clean()
        self.filemanager.backup(path,destination=destination, pathRegexIncludes=pathRegexIncludes,pathRegexExcludes=pathRegexExcludes,\
            childrenRegexExcludes=childrenRegexExcludes,fullcheck=fullcheck)
        self.commitMD()

    def _clean(self):
        for ddir in j.system.fs.listDirsInDir(self.mdpath,False,True,findDirectorySymlinks=False):
            if ddir.lower()!=".git":
                j.system.fs.removeDirTree(j.system.fs.joinPaths(self.mdpath,ddir))
        for ffile in j.system.fs.listFilesInDir(self.mdpath, recursive=False, followSymlinks=False):
            j.system.fs.remove(ffile)
        

    def backupRecipe(self,recipe):
        """
        do backup of sources as specified in recipe
        example recipe

        #when star will do for each dir
        /tmp/JSAPPS/apps : * : /DEST/apps
        #when no * then dir & below
        /tmp/JSAPPS/bin :  : /DEST/bin
        #now only for 1 subdir
        /tmp/JSAPPS/apps : asubdirOfApps : /DEST/apps

        """
        self._clean()
        self.filemanager.backupRecipe(recipe)
        self.commitMD()

    def commitMD(self):
        print("commit to git")
        self.gitclient.commit("backup %s"%j.base.time.getLocalTimeHRForFilesystem())
        if j.system.net.tcpPortConnectionTest(self.gitlab.addr,self.gitlab.port):
            #found gitlab
            print("push to git")
            self.gitclient.push()
        else:
            print("WARNING COULD NOT COMMIT CHANGES TO GITLAB, no connection found.\nDO THIS LATER!!!!!!!!!!!!!!!!!!!!!!")

