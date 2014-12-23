try:
# from urllib3.request import urlopen
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

import os
import tarfile
import sys
import shutil
import tempfile
import platform
import subprocess
import time
import fnmatch
import signal
from sys import argv
from subprocess import Popen, PIPE
import os, io
from threading import Thread
import Queue
import os
import smtplib

# from JumpScale import j

class InstallTools():
    def __init__(self,debug=False):
        if platform.system().lower()=="windows":
            self.TYPE="WIN"
            self.BASE="%s/"%os.environ["JSBASE"].replace("\\","/")
            while self.BASE[-1]=="/":
                self.BASE=self.BASE[:-1]
            self.BASE+="/"
            self.TMP=tempfile.gettempdir().replace("\\","/")
        else:
            self.TYPE="LINUX"
            if "JSBASE" in os.environ:
                self.BASE=os.environ["JSBASE"]
            self.TMP="/tmp"
        self.debug=False
        self.createDir("%s/jumpscaleinstall"%(self.TMP))
        self.debug=debug
        self._extratools=False

        if str(sys.excepthook).find("apport_excepthook")!=-1:
            #if we get here it means is std python excepthook (I hope)
            # print ("OUR OWN EXCEPTHOOK")
            sys.excepthook = self.excepthook

    def excepthook(self, ttype, pythonExceptionObject, tb):

        if isinstance(pythonExceptionObject, HaltException):
            sys.exit(1)

        # print "jumpscale EXCEPTIONHOOK"
        # if self.inException:
        #     print("ERROR IN EXCEPTION HANDLING ROUTINES, which causes recursive errorhandling behaviour.")
        #     print(pythonExceptionObject)
        #     return

        print ("WE ARE IN EXCEPTHOOL OF INSTALLTOOLS, DEVELOP THIS FURTHER")
        from IPython import embed
        print(44)
        embed()
        #@todo not working yet                

    def log(self,msg):
        if self.debug:
            print(msg)

    def readFile(self,filename): 
        """Read a file and get contents of that file
        @param filename: string (filename to open for reading )
        @rtype: string representing the file contents
        """
        with open(filename) as fp:
            data = fp.read()
        return data    

    def writeFile(self,path,content):
        fo = open(path, "w")
        fo.write( content )
        fo.close()

    def delete(self,path):

        if path.strip().rstrip("/") in ["","/","/etc","/root","/usr","/opt","/usr/bin","/usr/sbin","/opt/code"]:
            raise RuntimeError('cannot delete protected dirs')
        
        if path.find("/opt/code")!=-1:
            raise RuntimeError('cannot delete protected dirs')
        
        if self.debug:
            print(("delete: %s" % path))
        if os.path.exists(path) or os.path.islink(path):
            if os.path.isdir(path):
                #print "delete dir %s" % path           
                if os.path.islink(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            else:
                #print "delete file %s" % path           
                os.remove(path)

    def joinPaths(self,*args):
        return os.path.join(*args)

    # def copyTree(self,source,dest,deletefirst=False):
    #     if deletefirst:
    #         self.delete(dest)
    #     if self.debug:
    #         print("copy %s %s" % (source,dest))
    #     from IPython import embed
    #     print "DEBUG NOW ooo"
    #     embed()
        
    #     shutil.copytree(source,dest)

    def copyTree(self, source, dest, keepsymlinks = False, deletefirst = False, overwriteFiles=True,ignoredir=[".egg-info",".dist-info"],ignorefiles=[".egg-info"],rsync=True):
        if self.debug:
            print("copy %s %s" % (source,dest))
        if not self.exists(source):
            raise RuntimeError("copytree:Cannot find source:%s"%source)
        if rsync:
            excl=""
            for item in ignoredir:
                excl+="--exclude '*%s*/' "%item
            for item in ignorefiles:
                excl+="--exclude '*%s*' "%item
            excl+="--exclude '*.pyc' "
            excl+="--exclude '*.bak' "
            excl+="--exclude '*__pycache__*' "
            if dest[-1]!="/":
                dest+="/"
            if source[-1]!="/":
                source+="/"
            self.createDir(dest)
            cmd="rsync -aW --no-compress %s %s %s"%(excl,source,dest)           
            self.execute(cmd)
            return()
        else:
            old_debug=self.debug
            self.debug=False
            self._copyTree(source, dest, keepsymlinks, deletefirst, overwriteFiles,ignoredir=ignoredir,ignorefiles=ignorefiles)    
            self.debug=  old_debug

    def _copyTree(self, src, dst, keepsymlinks = False, deletefirst = False, overwriteFiles=True,ignoredir=[".egg-info","__pycache__"],ignorefiles=[".egg-info"]):
        """Recursively copy an entire directory tree rooted at src.
        The dst directory may already exist; if not,
        it will be created as well as missing parent directories
        @param src: string (source of directory tree to be copied)
        @param dst: string (path directory to be copied to...should not already exist)
        @param keepsymlinks: bool (True keeps symlinks instead of copying the content of the file)
        @param deletefirst: bool (Set to True if you want to erase destination first, be carefull, this can erase directories)
        @param overwriteFiles: if True will overwrite files, otherwise will not overwrite when destination exists
        """

        self.log('Copy directory tree from %s to %s'% (src, dst),6)
        if ((src is None) or (dst is None)):
            raise TypeError('Not enough parameters passed in system.fs.copyTree to copy directory from %s to %s '% (src, dst))
        if self.isDir(src):
            if ignoredir!=[]:
                for item in ignoredir:
                    if src.find(item)!=-1:
                        return
            names = os.listdir(src)
 
            if not self.exists(dst):
                self.createDir(dst)

            errors = []
            for name in names:
                #is only for the name
                name2=name

                srcname = self.joinPaths(src, name)
                dstname = self.joinPaths(dst, name2)
                if deletefirst and self.exists( dstname ):
                    if self.isDir( dstname , False ) :
                        self.removeDirTree( dstname )
                    if self.isLink(dstname):
                        self.unlink( dstname )

                if keepsymlinks and self.isLink(srcname):
                    linkto = self.readLink(srcname)
                    # self.symlink(linkto, dstname)#, overwriteFiles)
                    try:
                        os.symlink(linkto,dstname)
                    except:
                        pass
                        #@todo very ugly change
                elif self.isDir(srcname):
                    #print "1:%s %s"%(srcname,dstname)
                    self.copyTree(srcname, dstname, keepsymlinks, deletefirst,overwriteFiles=overwriteFiles ,ignoredir=ignoredir)
                else:
                    #print "2:%s %s"%(srcname,dstname)
                    extt=self.getFileExtension(srcname)
                    if extt=="pyc" or extt=="egg-info":
                        continue
                    if ignorefiles!=[]:
                        for item in ignorefiles:
                            if srcname.find(item)!=-1:
                                continue
                    self.copyFile(srcname, dstname, deletefirst=overwriteFiles)
        else:
            raise RuntimeError('Source path %s in system.fs.copyTree is not a directory'% src)


    def copyFile(self,source,dest,deletefirst=False):
        if deletefirst:
            self.delete(dest)
        if self.debug:
            print("copy %s %s" % (source,dest))
        shutil.copy(source,dest)

    def createDir(self,path):
        if self.debug:
            print(("createDir: %s" % path))
        if not os.path.exists(path) and not os.path.islink(path):
            os.makedirs(path)

    def changeDir(self, path,create=False):
        """Changes Current Directory
        @param path: string (Directory path to be changed to)
        """
        self.log('Changing directory to: %s'%path,6)
        if create:
            self.createDir(path)
        if self.exists(path):
            if self.isDir(path):
                os.chdir(path)
            else:
                raise ValueError("Path: %s in system.fs.changeDir is not a Directory"% path)
        else:
            raise RuntimeError("Path: %s in system.fs.changeDir does not exist"% path)

    def isDir(self, path, followSoftlink=False):
        """Check if the specified Directory path exists
        @param path: string
        @param followSoftlink: boolean
        @rtype: boolean (True if directory exists)
        """
        if self.isLink(path) :
            if not followSoftlink:
                return False
            else:
                link=self.readLink(path)
                return self.isDir(link)
        else:
            return os.path.isdir(path)

    def isExecutable(self,path):
         stat.S_IXUSR & statobj.st_mode


    # def readLink(self,path):
    #     """Works only for unix
    #     Return a string representing the path to which the symbolic link points.
    #     """
    #     while path[-1]=="/" or path[-1]=="\\":
    #         path=path[:-1]
    #     return os.readLink(path)
    
    def isFile(self, path, followSoftlink = False):
        """Check if the specified file exists for the given path
        @param path: string
        @param followSoftlink: boolean
        @rtype: boolean (True if file exists for the given path)
        """
        if self.isLink(path) :
            if not followSoftlink:
                return False
            else:
                link=self.readLink(path)
                return self.isFile(link)
        else:
            return os.path.isfile(path)

    def isLink(self, path,checkJunction=False):
        """Check if the specified path is a link
        @param path: string
        @rtype: boolean (True if the specified path is a link)
        """
        if path[-1]==os.sep:
            path=path[:-1]
        if ( path is None):
            raise TypeError('Link path is None in system.fs.isLink')

        if checkJunction and self.isWindows():
            cmd="junction %s" % path
            try:
                result=self.execute(cmd)
            except Exception as e:
                raise RuntimeError("Could not execute junction cmd, is junction installed? Cmd was %s."%cmd)
            if result[0]!=0:
                raise RuntimeError("Could not execute junction cmd, is junction installed? Cmd was %s."%cmd)
            if result[1].lower().find("substitute name")!=-1:
                return True
            else:
                return False
            
        if(os.path.islink(path)):
            # self.log('path %s is a link'%path,8)
            return True
        # self.log('path %s is not a link'%path,8)
        return False            
      
    def list(self,path):
        # self.log("list:%s"%path)
        if(self.isDir(path)):
            s=["%s/%s"%(path,item) for item in os.listdir(path)]
            s.sort()
            return s
        elif(self.isLink(path)):
            link=self.readLink(path)
            return self.list(link)
        else:
            raise ValueError("Specified path: %s is not a Directory in self.listDir"% path)

    def exists(self,path):
        return os.path.exists(path)

    def findDependencies(self,path,deps={}):
        excl=["libc.so","libpthread.so","libutil.so"]
        out=self.installtools.execute("ldd %s"%path)
        result=[]
        for item in [item.strip() for item in out.split("\n") if item.strip()!=""]:
            if item.find("=>")!=-1:
                link=item.split("=>")[1].strip()
                link=link.split("(")[0].strip()
                if self.exists(link):
                    name=os.path.basename(link)
                    if name not in deps:
                        print(link)
                        deps[name]=link
                        deps=self.findDependencies(link)
        return deps

    def copyDependencies(self,path,dest):
        self.installtools.createDir(dest)
        deps=self.findDependencies(path)
        for name in list(deps.keys()):
            path=deps[name]
            self.installtools.copydeletefirst(path,"%s/%s"%(dest,name))

    def symlink(self,src,dest,delete=False):
        """
        dest is where the link will be created pointing to src
        """
        if self.debug:
            print(("symlink: src:%s dest(islink):%s" % (src,dest)))        
            
        if self.isLink(dest):
            self.removesymlink(dest)
        
        if delete:
            if self.TYPE=="WIN":
                self.removesymlink(dest)
                self.delete(dest)
            else:
                self.delete(dest)
            
        if self.TYPE=="WIN":
            cmd="junction %s %s 2>&1 > null" % (dest,src)
            os.system(cmd)
            #raise RuntimeError("not supported on windows yet")
        else:
            dest=dest.rstrip("/")
            src=src.rstrip("/")
            if not self.exists(src):
                raise RuntimeError("could not find src for link:%s"%src)
            os.symlink(src,dest)

    def symlinkFilesInDir(self,src,dest,delete=True):
        for item in self.listFilesInDir(src, recursive=False,followSymlinks=True,listSymlinks=True):
            dest2="%s/%s"%(dest,self.getBaseName(item))
            dest2=dest2.replace("//","/")
            print(("link %s:%s"%(item,dest2)))
            self.symlink(item,dest2,delete=delete)


    def removesymlink(self,path):
        if self.TYPE=="WIN":
            try:            
                cmd="junction -d %s 2>&1 > null" % (path)
                print(cmd)
                os.system(cmd)
            except Exception as e:
                pass
        else:
            os.unlink(path.rstrip("/"))

    def getBaseName(self, path):
        """Return the base name of pathname path."""
        # self.log('Get basename for path: %s'%path,9)
        if path is None:
            raise TypeError('Path is not passed in system.fs.getDirName')
        try:
            return os.path.basename(path.rstrip(os.path.sep))
        except Exception as e:
            raise RuntimeError('Failed to get base name of the given path: %s, Error: %s'% (path,str(e)))

    def checkDirOrLinkToDir(self,fullpath):
        """
        check if path is dir or link to a dir
        """
        if not self.isLink(fullpath) and os.path.isdir(fullpath):
            return True
        if self.isLink(fullpath):
            link=self.readLink(fullpath)
            if self.isDir(link):
                return True
        return False

    def getDirName(self, path,lastOnly=False,levelsUp=None):
        """
        Return a directory name from pathname path.
        @param path the path to find a directory within
        @param lastOnly means only the last part of the path which is a dir (overrides levelsUp to 0)
        @param levelsUp means, return the parent dir levelsUp levels up
         e.g. ...getDirName("/opt/qbase/bin/something/test.py", levelsUp=0) would return something
         e.g. ...getDirName("/opt/qbase/bin/something/test.py", levelsUp=1) would return bin
         e.g. ...getDirName("/opt/qbase/bin/something/test.py", levelsUp=10) would raise an error
        """
        self.log('Get directory name of path: %s' % path,9)
        if path is None:
            raise TypeError('Path is not passed in system.fs.getDirName')
        dname=os.path.dirname(path)
        dname=dname.replace("/",os.sep)
        dname=dname.replace("//",os.sep)
        dname=dname.replace("\\",os.sep)
        if lastOnly:
            dname=dname.split(os.sep)[-1]
            return dname
        if levelsUp!=None:
            parts=dname.split(os.sep)
            if len(parts)-levelsUp>0:
                return parts[len(parts)-levelsUp-1]
            else:
                raise RuntimeError ("Cannot find part of dir %s levels up, path %s is not long enough" % (levelsUp,path))
        return dname+os.sep

    def readLink(self, path):
        """Works only for unix
        Return a string representing the path to which the symbolic link points.
        """
        while path[-1]=="/" or path[-1]=="\\":
            path=path[:-1]
        # self.log('Read link with path: %s'%path,8)
        if path is None:
            raise TypeError('Path is not passed in system.fs.readLink')
        if self.isUnix():
            try:
                return os.readlink(path)
            except Exception as e:
                raise RuntimeError('Failed to read link with path: %s \nERROR: %s'%(path, str(e)))
        elif self.isWindows():
            raise RuntimeError('Cannot readLink on windows')

    def removeLinks(self,path):
        """
        find all links & remove
        """
        if not self.exists(path):
            return
        items=self._listAllInDir(path=path, recursive=True, followSymlinks=False,listSymlinks=True)
        items=[item for item in items[0] if self.isLink(item)]
        for item in items:
            self.unlink(item)        

    def _listInDir(self, path,followSymlinks=True):
        """returns array with dirs & files in directory
        @param path: string (Directory path to list contents under)
        """
        if path is None:
            raise TypeError('Path is not passed in system.fs.listDir')
        if(self.exists(path)):
            if(self.isDir(path)) or (followSymlinks and self.checkDirOrLinkToDir(path)):
                names = os.listdir(path)
                return names
            else:
                raise ValueError("Specified path: %s is not a Directory in system.fs.listDir"% path)
        else:
            raise RuntimeError("Specified path: %s does not exist in system.fs.listDir"% path)

    def listDirsInDir(self,path,recursive=False,dirNameOnly=False,findDirectorySymlinks=True):
        """ Retrieves list of directories found in the specified directory
        @param path: string represents directory path to search in
        @rtype: list
        """
        # self.log('List directories in directory with path: %s, recursive = %s' % (path, str(recursive)),9)

        #if recursive:
            #if not self.exists(path):
                #raise ValueError('Specified path: %s does not exist' % path)
            #if not self.isDir(path):
                #raise ValueError('Specified path: %s is not a directory' % path)
            #result = []
            #os.path.walk(path, lambda a, d, f: a.append('%s%s' % (d, os.path.sep)), result)
            #return result

        files=self._listInDir(path,followSymlinks=True)
        filesreturn=[]
        for file in files:
            fullpath=os.path.join(path,file)
            if (findDirectorySymlinks and self.checkDirOrLinkToDir(fullpath)) or self.isDir(fullpath):
                if dirNameOnly:
                    filesreturn.append(file)
                else:
                    filesreturn.append(fullpath)
                if recursive:
                    filesreturn.extend(self.listDirsInDir(fullpath,recursive,dirNameOnly,findDirectorySymlinks))
        return filesreturn

    def listFilesInDir(self, path, recursive=False, filter=None, minmtime=None, maxmtime=None,depth=None, case_sensitivity='os',exclude=[],followSymlinks=True,listSymlinks=False):
        """Retrieves list of files found in the specified directory
        @param path:       directory path to search in
        @type  path:       string
        @param recursive:  recursively look in all subdirs
        @type  recursive:  boolean
        @param filter:     unix-style wildcard (e.g. *.py) - this is not a regular expression
        @type  filter:     string
        @param minmtime:   if not None, only return files whose last modification time > minmtime (epoch in seconds)
        @type  minmtime:   integer
        @param maxmtime:   if not None, only return files whose last modification time < maxmtime (epoch in seconds)
        @Param depth: is levels deep wich we need to go
        @type  maxmtime:   integer
        @Param exclude: list of std filters if matches then exclude
        @rtype: list
        """
        if depth!=None:
            depth=int(depth)
        # self.log('List files in directory with path: %s' % path,9)
        if depth==0:
            depth=None
        # if depth != None:
        #     depth+=1
        filesreturn,depth=self._listAllInDir(path, recursive, filter, minmtime, maxmtime,depth,type="f", case_sensitivity=case_sensitivity,exclude=exclude,followSymlinks=followSymlinks,listSymlinks=listSymlinks)
        return filesreturn

    def listFilesAndDirsInDir(self, path, recursive=False, filter=None, minmtime=None, maxmtime=None,depth=None,type="fd",followSymlinks=True,listSymlinks=False):
        """Retrieves list of files found in the specified directory
        @param path:       directory path to search in
        @type  path:       string
        @param recursive:  recursively look in all subdirs
        @type  recursive:  boolean
        @param filter:     unix-style wildcard (e.g. *.py) - this is not a regular expression
        @type  filter:     string
        @param minmtime:   if not None, only return files whose last modification time > minmtime (epoch in seconds)
        @type  minmtime:   integer
        @param maxmtime:   if not None, only return files whose last modification time < maxmtime (epoch in seconds)
        @Param depth: is levels deep wich we need to go
        @type  maxmtime:   integer
        @param type is string with f & d inside (f for when to find files, d for when to find dirs)
        @rtype: list
        """
        if depth!=None:
            depth=int(depth)
        self.log('List files in directory with path: %s' % path,9)
        if depth==0:
            depth=None
        # if depth != None:
        #     depth+=1
        filesreturn,depth=self._listAllInDir(path, recursive, filter, minmtime, maxmtime,depth,type=type,followSymlinks=followSymlinks,listSymlinks=listSymlinks)
        return filesreturn


    def _listAllInDir(self, path, recursive, filter=None, minmtime=None, maxmtime=None,depth=None,type="df", case_sensitivity='os',exclude=[],followSymlinks=True,listSymlinks=True):
        """
        # There are 3 possible options for case-sensitivity for file names
        # 1. `os`: the same behavior as the OS
        # 2. `sensitive`: case-sensitive comparison
        # 3. `insensitive`: case-insensitive comparison
        """

        dircontent = self._listInDir(path)
        filesreturn = []

        if case_sensitivity.lower() == 'sensitive':
            matcher = fnmatch.fnmatchcase
        elif case_sensitivity.lower() == 'insensitive':
            def matcher(fname, pattern):
                return fnmatch.fnmatchcase(fname.lower(), pattern.lower())
        else:
            matcher = fnmatch.fnmatch

        for direntry in dircontent:
            fullpath = self.joinPaths(path, direntry)
                

            if followSymlinks:
                if self.isLink(fullpath):
                    fullpath=self.readLink(fullpath)

            if self.isFile(fullpath) and "f" in type:
                includeFile = False
                if (filter is None) or matcher(direntry, filter):
                    if (minmtime is not None) or (maxmtime is not None):
                        mymtime = os.stat(fullpath)[ST_MTIME]
                        if (minmtime is None) or (mymtime > minmtime):
                            if (maxmtime is None) or (mymtime < maxmtime):
                                includeFile = True
                    else:
                        includeFile = True
                if includeFile:
                    if exclude!=[]:
                        for excludeItem in exclude:
                            if matcher(direntry, excludeItem):
                                includeFile=False
                    if includeFile:
                        filesreturn.append(fullpath)                    
            elif self.isDir(fullpath):
                if "d" in type:                                                                 
                    if not(listSymlinks==False and self.isLink(fullpath)):
                        filesreturn.append(fullpath)
                if recursive:
                    if depth!=None and depth!=0:
                        depth=depth-1
                    if depth==None or depth!=0:
                        exclmatch=False
                        if exclude!=[]:
                            for excludeItem in exclude:
                                if matcher(fullpath, excludeItem):
                                    exclmatch=True
                        if exclmatch==False:            
                            if not(followSymlinks==False and self.isLink(fullpath)):
                                r,depth = self._listAllInDir(fullpath, recursive, filter, minmtime, maxmtime,depth=depth,type=type,exclude=exclude,followSymlinks=followSymlinks,listSymlinks=listSymlinks)
                                if len(r) > 0: 
                                    filesreturn.extend(r)
            elif self.isLink(fullpath) and followSymlinks==False and listSymlinks:
                filesreturn.append(fullpath)                

        return filesreturn,depth


    def getParent(self, path):
        """
        Returns the parent of the path:
        /dir1/dir2/file_or_dir -> /dir1/dir2/
        /dir1/dir2/            -> /dir1/
        @todo why do we have 2 implementations which are almost the same see getParentDirName()
        """
        parts = path.split(os.sep)
        if parts[-1] == '':
            parts=parts[:-1]
        parts=parts[:-1]
        if parts==['']:
            return os.sep
        return os.sep.join(parts)

    def getFileExtension(self,path):
        extcand=path.split(".")
        if len(extcand)>0:
            ext=extcand[-1]
        else:
            ext=""
        return ext

    def chown(self,path,user):
        from pwd import getpwnam  
        getpwnam(user)[2]
        uid=getpwnam(user).pw_uid
        gid=getpwnam(user).pw_gid
        os.chown(path, uid, gid)
        for root, dirs, files in os.walk(path):  
            for ddir in dirs:  
                path = os.path.join(root, ddir)
                try:
                    os.chown(path, uid, gid)
                except Exception as e:
                    if str(e).find("No such file or directory")==-1:
                        raise RuntimeError("%s"%e)                
            for file in files:
                path = os.path.join(root, file)
                try:
                    os.chown(path, uid, gid)
                except Exception as e:
                    if str(e).find("No such file or directory")==-1:
                        raise RuntimeError("%s"%e)

    def chmod(self,path,permissions):
        """
        @param permissions e.g. 0o660 (USE OCTAL !!!)
        """
        os.chmod(path,permissions)
        for root, dirs, files in os.walk(path):  
            for ddir in dirs:  
                path = os.path.join(root, ddir)
                try:
                    os.chmod(path,permissions)
                except Exception as e:
                    if str(e).find("No such file or directory")==-1:
                        raise RuntimeError("%s"%e)
                    
            for file in files:
                path = os.path.join(root, file)
                try:
                    os.chmod(path,permissions)
                except Exception as e:
                    if str(e).find("No such file or directory")==-1:
                        raise RuntimeError("%s"%e)


    #########NON FS

    def download(self,url,to):
        os.chdir(self.TMP)
        print(('Downloading %s ' % (url)))
        handle = urlopen(url)
        with open(to, 'wb') as out:
            while True:
                data = handle.read(1024)
                if len(data) == 0: break
                out.write(data)
        handle.close()
        out.close()

    def chdir(seld,ddir):
        os.chdir(ddir)

    # def execute(self,command, timeout=60,tostdout=True):

    #     try:
    #         proc = subprocess.Popen(command, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=True)
    #     except Exception,e:
    #         raise RuntimeError("Cannot execute cmd:%s, could not launch process, error was %s"%(command,e))
            
    #     poll_seconds = .250
    #     deadline = time.time()+timeout
    #     while time.time() < deadline and proc.poll() == None:
    #         time.sleep(poll_seconds)

    #     if proc.poll() == None:
    #         if float(sys.version[:3]) >= 2.6:
    #             proc.terminate()
    #         raise RuntimeError("Cannot execute cmd:%s, timeout"%(command))

    #     stdout, stderr = proc.communicate()

    #     if stdout.strip()=="":
    #         stdout=stderr

    #     if proc.returncode != 0:
    #         raise RuntimeError("Cannot execute cmd:%s, error was %s"%(command,stderr))

    #     return stdout

    def log(self,msg,level=0):
        print(msg)

    def isUnix(self):
        if sys.platform.lower().find("linux")!=-1:
            return True
        return False


    def isWindows(self):
        if sys.platform.lower().find("linux")==1:
            return True
        return False

    def executeCmds(self,cmdstr, outputStdout=True, outputStderr=True,useShell = True,log=True,cwd=None,timeout=60,errors=[],ok=[],captureout=True,dieOnNonZeroExitCode=True):        
        rc_=""
        out_=""
        err_=""
        for cmd in cmdstr.split("\n"):
            if cmd.strip()=="" or cmd[0]=="#":
                continue
            rc,out,err=self.execute(cmd, outputStdout, outputStderr,useShell ,log,cwd,timeout,errors,ok,captureout,dieOnNonZeroExitCode)
            rc_+=str(rc)
            out_+=out
            err_+=err

        return rc_,out_,err_


    def sendmail(self,ffrom,to,subject,msg,smtpuser,smtppasswd,smtpserver="smtp.mandrillapp.com",port=587,html=""):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart('alternative')

        msg['Subject'] = subject
        msg['From']    =ffrom
        msg['To']      = to

        if msg!="":
            part1 = MIMEText(str(msg), 'plain')
            msg.attach(part1)
        
        if html!="":
            part2 = MIMEText(html, 'html')            
            msg.attach(part2)

        s = smtplib.SMTP(smtpserver, port)

        s.login(smtpuser, smtppasswd)
        s.sendmail(msg['From'], msg['To'], msg.as_string())

        s.quit()        

    def execute(self, command , outputStdout=True, outputStderr=True, useShell=True, log=True, cwd=None, timeout=60, errors=[], ok=[], captureout=True, dieOnNonZeroExitCode=True):
        """
        @param errors is array of statements if found then exit as error
        """
        # print "EXEC:"
        # print command
        os.environ["PYTHONUNBUFFERED"]="1"
        ON_POSIX = 'posix' in sys.builtin_module_names
 
        popenargs={}        
        if not subprocess.mswindows:
            # Reset all signals before calling execlp but after forking. This
            # fixes Python issue 1652 (http://bugs.python.org/issue1652) and
            # jumpscale ticket 189
            def reset_signals():
                '''Reset all signals to SIG_DFL'''
                for i in xrange(1, signal.NSIG):
                    if signal.getsignal(i) != signal.SIG_DFL:
                        try:
                            signal.signal(i, signal.SIG_DFL)
                        except RuntimeError:
                            # Skip, can't set this signal
                            pass
            popenargs["preexec_fn"]=reset_signals

        p=Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=ON_POSIX, \
                    shell=useShell, env=os.environ,universal_newlines=True,cwd=cwd,bufsize=0,**popenargs)

        sout = io.open(p.stdout.fileno(), 'rb', closefd=False)
        serr = io.open(p.stderr.fileno(), 'rb', closefd=False)
        def Pump(sout,serr):
            queue = Queue.Queue()
            def stdout1():
                while True:
                    # buf = sout.read1(8192)
                    buf = sout.readline()
                    if len(buf)>0:
                        queue.put( ("O",buf) )
                    else:
                        queue.put( (None,None) )
                        return
            def strerr1():
                while True:
                    # buf = serr.read1(8192)
                    buf = serr.readline()
                    if len(buf)>0:
                        queue.put( ("E",buf) )
                    else:
                        queue.put((None, None) )
                        return

            t1 = Thread(target=stdout1)
            t1.setDaemon(True)
            t1.start()
            t2 = Thread(target=strerr1)
            t2.setDaemon(True)
            t2.start()    
            return queue,t1,t2 
            
        inp,t1,t2=Pump(sout,serr)

        start=time.time()

        err=""
        out=""
        rc=1000


        while p.poll() is None or inp.empty()==False:
            # App still working
            # print p.poll()
            try:
                chan,line = inp.get(timeout = 1.0)
                if ok<>[]:
                    for item in ok:
                        if line.find(item)!=-1:
                            rc=0
                            break
                if errors<>[]:
                    # if captureout==False:
                    #     out=line
                    for item in errors:
                        if line.find(item)!=-1:
                            rc=997
                            break
                        # if err.find(item)!=-1:
                        #     rc=1
                        #     break  
                    if rc==997 or rc==0:
                        break

                if line==None:
                    break

                if chan=='O':
                    if outputStdout:
                        print (line)
                    if captureout:
                        out+=line
                elif chan=='E':
                    if outputStderr:
                        print ("ERR:%s"%line)
                    if captureout:
                        err+=line
            except Queue.Empty:
                pass
            if time.time()>start+timeout:
                print "TIMEOUT"
                rc=999
                p.kill()
                
                break
        if rc<>999:
            (output2,error2) = p.communicate()
            out+=output2
            err==error2
        if rc==1000:
            rc = p.returncode
            if rc==0 and err<>"":
                rc=998

        if rc>0 and dieOnNonZeroExitCode:
            if err<>"":
                raise RuntimeError("Could not execute cmd:\n'%s'\nerr:\n%s"%(command,err))
            else:
                raise RuntimeError("Could not execute cmd:\n'%s'\nout:\n%s"%(command,out))

        return rc,out,err
        


    # def execute(self, command , dieOnNonZeroExitCode=True, outputStdout=True, outputStderr=True,useShell = True,log=True,cwd=None):
    #     """Executes a command, returns the exitcode and the output
    #     @param command: command to execute
    #     @param dieOnNonZeroExitCode: boolean to die if got non zero exitcode
    #     @param outputToStdout: boolean to show/hide output to stdout
    #     @param ignoreErrorOutput standard stderror is added to stdout in out result, if you want to make sure this does not happen put on True
    #     @rtype: integer represents the exitcode plus the output of the executed command
    #     if exitcode is not zero then the executed command returned with errors
    #     """
    #     # Since python has no non-blocking readline() call, we implement it ourselves
    #     # using the following private methods.
    #     #
    #     # We choose for line buffering, i.e. whenever we receive a full line of output (terminated by \n)
    #     # on stdout or stdin of the child process, we log it
    #     #
    #     # When the process terminates, we log the final lines (and add a \n to them)
    #     if log:
    #         self.log("exec:%s" % command)
    #     def _logentry(entry):
    #         if outputToStdout:
    #             self.log(entry)

    #     def _splitdata(data):
    #         """ Split data in pieces separated by \n """
    #         lines = data.split("\n")
    #         return lines[:-1], lines[-1]

    #     def _logoutput(data, OUT_LINE, ERR_LINE):
    #         [lines, partialline] = _splitdata(data)
    #         if lines:
    #             lines[0] = OUT_LINE + lines[0]
    #         else:
    #             partialline = OUT_LINE + partialline
    #         OUT_LINE = ""
    #         if partialline:
    #             OUT_LINE = partialline
    #         for x in lines:
    #             _logentry(x,3)
    #         return OUT_LINE, ERR_LINE

    #     def _logerror(data, OUT_LINE, ERR_LINE):
    #         [lines, partialline] = _splitdata(data)
    #         if lines:
    #             lines[0] = ERR_LINE + lines[0]
    #         else:
    #             partialline = ERR_LINE + partialline
    #         ERR_LINE = ""
    #         if partialline:
    #             ERR_LINE = partialline
    #         for x in lines:
    #             _logentry(x,4)
    #         return OUT_LINE, ERR_LINE

    #     def _flushlogs(OUT_LINE, ERR_LINE):
    #         """ Called when the child process closes. We need to get the last
    #             non-\n terminated pieces of the stdout and stderr streams
    #         """
    #         if OUT_LINE:
    #             _logentry(OUT_LINE,3)
    #         if ERR_LINE:
    #             _logentry(ERR_LINE,4)

    #     if command is None:
    #         raise ValueError('Error, cannot execute command not specified')

    #     try:
    #         import errno
    #         if self.isUnix():
    #             import subprocess
    #             # import signal
    #             # try:
    #             #     signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    #             # except Exception as ex:
    #             #     print('failed to set child signal, error %s'%ex, 2)

    #             childprocess = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False, \
    #                 shell=useShell, env=os.environ,universal_newlines=True,cwd=cwd,bufsize=0)
    #             (output,error) = childprocess.communicate()
    #             exitcode = childprocess.returncode
    #             poll=childprocess.poll()
    #             print "EXEC DONE1"
    #             print "exitcode:%s"%exitcode
    #             print "output:'%s'"%output   

    #             from IPython import embed
    #             print "DEBUG NOW ooo"
    #             embed()
    #             p
                

    #         elif self.isWindows():
    #             import subprocess, win32pipe, msvcrt, pywintypes

    #             # For some awkward reason you need to include the stdin pipe, or you get an error deep inside
    #             # the subprocess module if you use QRedirectStdOut in the calling script
    #             # We do not use the stdin.
    #             childprocess = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=False, shell=useShell, env=os.environ)
    #             output = ""; OUT_LINE = ""; ERR_LINE = ""
    #             childRunning = True

    #             while childRunning:
    #                 stdoutData = childprocess.stdout.readline() # The readline method will block until data is received on stdout, or the stdout pipe has been destroyed. (Will return empty string)
    #                                                             # Only call processes that release their stdout pipe when exiting, otherwise the method will not return when the process completed.
    #                                                             # When the called process starts another process and marks its handle of the stdout pipe as inheritable, the pipe will not be destroyed before both processes end.
    #                 if stdoutData != '':
    #                     output = output + stdoutData
    #                     (OUT_LINE, ERR_LINE) = _logoutput(stdoutData, OUT_LINE, ERR_LINE)
    #                 else: # Did not read any data on channel
    #                     if childprocess.poll() != None: # Will return a number if the process has ended, or None if it's running.
    #                         childRunning = False

    #             exitcode = childprocess.returncode
    #             error = "Error output redirected to stdout."

    #         else:
    #             raise RuntimeError("Non supported OS for self.execute()")

    #     except Exception as e:
    #         print e
    #         raise RuntimeError("ERROR IN EXECUTION, SHOULD NOT GET HERE.")
        
    #     output=output.decode('utf8')#'ascii')  
    #     print "EXEC DONE2"
    #     print "exitcode:%s"%exitcode
    #     print "output:'%s'"%output          
    #     error=error.decode('utf8')#'ascii')

    #     if (int(exitcode)!=0 or str(error)!=""):
    #         errmsg="**ERROR**: execute cmd '%s' exitcode(%s)\nOutput:%s\nError:%s\n" % (command,exitcode, output, error)  
    #         if dieOnNonZeroExitCode:                
    #             print (errmsg)
    #             raise RuntimeError(errmsg)
    #         if not ignoreErrorOutput:
    #             print (errmsg)
            
    #     return output        

    def executeInteractive(self,command):
        exitcode = os.system(command)
        return exitcode

    def downloadExpandTarGz(self,url,destdir,deleteDestFirst=True,deleteSourceAfter=True):
        print((self.getBaseName(url)))
        tmppath=self.getTmpPath(self.getBaseName(url))
        self.download(url,tmppath)
        self.expandTarGz(tmppath,destdir)

    def expandTarGz(self,path,destdir,deleteDestFirst=True,deleteSourceAfter=False):

        self.lastdir=os.getcwd()
        os.chdir(self.TMP)
        basename=os.path.basename(path)
        if basename.find(".tar.gz")==-1:
            raise RuntimeError("Can only expand a tar gz file now %s"%path)
        tarfilename=".".join(basename.split(".gz")[:-1])
        self.delete(tarfilename)
        
        if deleteDestFirst:
            self.delete(destdir)

        if self.TYPE=="WIN":
            cmd="gzip -d %s" % path
            os.system(cmd)
        else:
            handle = gzip.open(path)
            with open(tarfilename, 'w') as out:
                for line in handle:
                    out.write(line)
            out.close()
            handle.close()

        t = tarfile.open(tarfilename, 'r')
        t.extractall(destdir)    
        t.close()

        self.delete(tarfilename)

        if deleteSourceAfter:
            self.delete(path)

        os.chdir(self.lastdir)
        self.lastdir=""

    def getTmpPath(self,filename):
        return "%s/jumpscaleinstall/%s"%(self.TMP,filename)

    def downloadJumpScaleCore(self,dest):
        #csid=getLastChangeSetBitbucket()        
        self.download ("https://bitbucket.org/jumpscale/jumpscale-core/get/default.tar.gz","%s/pl6core.tgz"%self.TMP)
        self.expand("%s/pl6core.tgz"%self.TMP,dest)
            
    def getPythonSiteConfigPath(self):
        minl=1000000
        result=""
        for item in sys.path:
            if len(item)<minl and item.find("python")!=-1:
                result=item
                minl=len(item)
        return result

    def getTimeEpoch(self):
        '''
        Get epoch timestamp (number of seconds passed since January 1, 1970)
        '''
        return int(time.time())

    def pullGitRepo(self,url,dest=None,login=None,passwd=None,depth=None,ignorelocalchanges=False,reset=False,branch="master"):
        """
        will clone or update repo
        if dest == None then clone underneath: /opt/code/$type/$account/$repo
        will ignore changes !!!!!!!!!!!
        """
        if url.startswith("https://"):
            pre="https://"
            url2=url[len(pre):]
        elif url.startswith("http://"):
            pre="http://"
            url2=url[len(pre):]
        else:
            raise RuntimeError("Url needs to start with 'http(s)://'")

        if login!=None:            
            url="%s%s:%s@%s"%(pre,login,passwd,url2)

        if dest==None:
            url3=url2.strip(" /")
            ttype,account,repo=url3.split("/",3)
            if ttype.find(".")!=-1:
                ttype=ttype.split(".",1)[0]
            dest="/opt/code/%s/%s/%s/"%(ttype.lower(),account.lower(),repo.lower().replace(".git",""))

        if reset:
            self.delete(dest)

        self.createDir(dest)
        checkdir="%s/.git"%(dest)
        if self.exists(checkdir):
            if ignorelocalchanges:
                print(("git pull, ignore changes %s -> %s"%(url,dest)))
                cmd="cd %s;git fetch"%dest
                if depth!=None:
                    cmd+=" --depth %s"%depth    
                self.executeInteractive(cmd)
                self.executeInteractive("cd %s;git reset --hard origin/%s"%(dest,branch))
            else:
                #pull
                print(("git pull %s -> %s"%(url,dest)))
                cmd="cd %s;git pull origin %s"%(dest,branch)
                self.executeInteractive(cmd)
        else:
            print(("git clone %s -> %s"%(url,dest)))
            cmd="cd %s;git clone -b %s --single-branch %s %s"%(dest,branch,url,dest)
            if depth!=None:
                cmd+=" --depth %s"%depth        
            self.executeInteractive(cmd)

        return dest

    def getGitReposListLocal(self,ttype="",account="",name="",errorIfNone=True):
        repos={}
        for top in self.listDirsInDir("/opt/code/", recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
            if ttype!="" and ttype!=top:
                continue
            for accountfound in self.listDirsInDir("/opt/code/%s"%top, recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
                if account!="" and account!=accountfound:
                    continue                
                accountfounddir="/opt/code/%s/%s"%(top,accountfound)
                for reponame in self.listDirsInDir("/opt/code/%s/%s"%(top,accountfound), recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
                    if name!="" and name!=reponame:
                        continue                          
                    repodir="/opt/code/%s/%s/%s"%(top,accountfound,reponame)
                    if self.exists(path="%s/.git"%repodir):
                        repos[reponame]=repodir
        if len(list(repos.keys()))==0:
            raise RuntimeError("Cannot find git repo '%s':'%s':'%s'"%(ttype,account,name))
        return repos


    def pushGitRepos(self,message,name="",update=True,ttype="",account=""):
        """
        if name specified then will look under code dir if repo with path can be found
        if not or more than 1 there will be error
        """
        repos=self.getGitReposListLocal(ttype,account,name)
        for name,path in list(repos.items()):
            print(("push git repo:%s"%path))
            cmd="cd %s;git add . -A"%(path)
            self.executeInteractive(cmd)
            cmd="cd %s;git commit -m \"%s\""%(path,message)
            self.executeInteractive(cmd)
            if update:
                cmd="cd %s;git pull"%(path)
                self.executeInteractive(cmd)
            cmd="cd %s;git push"%(path)
            self.executeInteractive(cmd)

    def updateGitRepos(self,ttype="",account="",name="",message=""):
        repos=self.getGitReposListLocal(ttype,account,name)
        for name,path in list(repos.items()):
            print(("push git repo:%s"%path))
            cmd="cd %s;git add . -A"%(path)
            self.executeInteractive(cmd)
            cmd="cd %s;git commit -m \"%s\""%(path,message)
            self.executeInteractive(cmd)
            cmd="cd %s;git pull"%(path)
            self.executeInteractive(cmd)

    def changeLoginPasswdGitRepos(self,ttype,login,passwd):
        """
        walk over all git repo's found in account & change login/passwd
        """
        for reponame,repopath in list(self.getGitReposListLocal(ttype).items()):
            import re
            configpath="%s/.git/config"%repopath
            text=self.readFile(configpath)
            text2=text
            for item in re.findall(re.compile(r'//.*@%s'%ttype), text):
                newitem="//%s:%s@%s"%(login,passwd,ttype)
                text2=text.replace(item,newitem)
            if text2!=text:
                print(("changed login/passwd on %s"%configpath))
                self.writeFile(configpath,text2)            


############# package installation

    def installJS(self,base="/opt/jumpscale7",clean=False,insystem=False,pythonversion=2,web=False,copybinary=True):
        """
        @param pythonversion is 2 or 3
        if 3 and base not specified then base becomes /opt/jumpscale73
        """
        print(("Install Jumpscale in %s"%base))
        if clean:
            self.cleanSystem()

        if pythonversion==3 and base=="/opt/jumpscale7":
            base="/opt/jumpscale73"

        self.debug=True

        if pythonversion==2:
            gitbase="base_python"
        else:
            gitbase="base_python3"
        
        print ("pull binaries")
        self.pullGitRepo("http://git.aydo.com/binary/%s"%gitbase,depth=1)        

        print ("copy binaries")
        # self.createDir(base)        
        if copybinary:
            self.copyTree("/opt/code/git/binary/%s/root/"%gitbase,base)

        print ("pull core")
        self.pullGitRepo("https://github.com/Jumpscale/jumpscale_core7",depth=1)    
        src="/opt/code/github/jumpscale/jumpscale_core7/lib/JumpScale"
        self.debug=False
        if pythonversion==2:
            dest="/usr/local/lib/python2.7/dist-packages/JumpScale"
        else:
            dest="/usr/local/lib/python3.4/dist-packages/JumpScale"
        if insystem or not self.exists(dest):            
            self.symlink(src, dest)

        self.createDir("%s/lib"%base)
        self.createDir("%s/bin"%base)
        self.createDir("%s/hrd/system"%base)
        self.createDir("%s/hrd/apps"%base)

        dest="%s/lib/JumpScale"%base
        print ("link: '%s' -> '%s'"%(src,dest))
        self.symlink(src, dest)
        src="/opt/code/github/jumpscale/jumpscale_core7/shellcmds"
        desttest="/usr/local/bin/js"
        if insystem or not self.exists(desttest):
            dest="/usr/local/bin"
            self.symlinkFilesInDir(src, dest)
        
        dest="%s/bin"%base
        self.symlinkFilesInDir(src, dest)

        print ("copycore")
        self.copyTree("/opt/code/github/jumpscale/jumpscale_core7/jsbox/cfg/hrd/","%s/hrd/"%base)

        for item in ["InstallTools","ExtraTools"]:
            src="/opt/code/github/jumpscale/jumpscale_core7/install/%s.py"%item
            dest="%s/lib/%s.py"%(base,item)
            self.symlink(src, dest) 
            if insystem:      
                dest="/usr/local/lib/python2.7/dist-packages/%s.py"%(item)
                self.symlink(src, dest) 

        if web:
            if pythonversion==2:
                gitbase="web_python"
            else:
                gitbase="web_python3"
            self.pullGitRepo("http://git.aydo.com/binary/%s"%gitbase,depth=1)  
            self.copyTree("/opt/code/git/binary/%s/root/"%gitbase,base) 


        if pythonversion==2:
            basedir="/opt/jumpscale7"
        else:
            basedir="/opt/jumpscale73"

        self._writeenv(basedir=basedir,insystem=insystem)

        if not insystem:
            sys.path=[]
        sys.path.insert(0,"%s/lib"%basedir)

        from JumpScale import j

        #make sure all configured paths are created
        for item in j.application.config.getListFromPrefix("system.paths"):
            self.createDir(item)

        self.createDir("%s/jpackage_actions"%j.application.config.get("system.paths.base"))

        print("Get jpackages metadata.")
        self.pullGitRepo("https://github.com/Jumpscale/jp_jumpscale7",depth=1)

        p="/opt/jumpscale7/hrd/system/_whoami_template.hrd"
        p2="/opt/jumpscale7/hrd/system/whoami.hrd"
        if not j.system.fs.exists(path=p2):
            j.do.copyFile(p,p2)

        print ("install was successfull")
        if pythonversion==2:
            print ("to use do 'source %s/env.sh;ipython'"%base)
        else:
            print ("to use do 'source %s/env.sh;ipython3'"%base)


    def _writeenv(self,basedir,insystem=False):


        C="""
paths.base=$base
paths.bin=$(paths.base)/bin
paths.tmp=/tmp/jumpscale
paths.code=/opt/code
paths.lib=$(paths.base)/lib

paths.python.lib.js=$(paths.lib)/JumpScale
paths.python.lib.ext=$(paths.base)/libext
paths.app=$(paths.base)/app
paths.var=$(paths.base)/var
paths.log=$(paths.var)/log
paths.pid=$(paths.var)/pid

paths.cfg=$(paths.base)/cfg
paths.hrd=$(paths.base)/hrd
"""
        C=C.replace("$base",basedir.rstrip("/"))
        self.writeFile("%s/hrd/system/system.hrd"%basedir,C)

        C="""
export PATH=$base/bin:$PATH
export JSBASE=$base
export PYTHONPATH=$base/lib:$base/lib/lib-dynload/:$base/bin:$base/lib/python.zip:$base/lib/plat-x86_64-linux-gnu
#export PYTHONHOME=$base
export LD_LIBRARY_PATH=$base/bin    
"""
        C=C.replace("$base",basedir)
        self.writeFile("%s/env.sh"%basedir,C)

        C2="""
#!/bin/bash
set -x
$ENV
echo sandbox:$base
# echo $base/bin/python "$@"
$base/bin/python "$@"
"""
        C2=C2.replace("$ENV",C)
        C2=C2.replace("$base",basedir)
        dest="%s/bin/jspython"%basedir
        self.delete(dest)
        self.writeFile(dest,C2)
        self.chmod(dest, 0o770)

        if insystem:
            C2="""
#!/bin/bash
set -ex
#export PYTHONPATH=$base/lib:$base/lib/lib-dynload/:$base/bin:$base/lib/python.zip:$base/lib/plat-x86_64-linux-gnu:$PYTHONPATH
/usr/bin/python "$@"
"""            
            C2=C2.replace("$base",basedir)
            dest="/usr/local/bin/jspython"
            self.delete(dest)
            self.writeFile(dest,C2)
            self.chmod(dest, 0o770)

        #change site.py file        
        def changesite(path):
            if self.exists(path=path):
                C=self.readFile(path)
                out=""
                for line in C.split("\n"):
                    if line.find("ENABLE_USER_SITE")==0:
                        line="ENABLE_USER_SITE = False"
                    if line.find("USER_SITE")==0:
                        line="USER_SITE = False"
                    if line.find("USER_BASE")==0:
                        line="USER_BASE = False"

                    out+="%s\n"%line
                self.writeFile(path,out)
        changesite("%s/lib/site.py"%basedir)
        # if insystem:
        #     changesite("/usr/local/lib/python2.7/dist-packages/site.py"%basedir)


    def loadScript(self,path):
        print(("load jumpscript: %s"%path))
        source = j.system.fs.fileGetContents(path)
        out,tags=self._preprocess(source)        
        md5sum=j.tools.hash.md5_string(out)
        modulename = 'JumpScale.jumpscript_%s' % md5sum

        codepath=j.system.fs.joinPaths(j.dirs.tmpDir,"jumpscripts","%s.py"%md5sum)
        j.system.fs.writeFile(filename=codepath,contents=out)

        linecache.checkcache(codepath)
        self.module = imp.load_source(modulename, codepath)

        self.author=getattr(self.module, 'author', "unknown")
        self.organization=getattr(self.module, 'organization', "unknown")
        self.version=getattr(self.module, 'version', 0)
        self.modtime=getattr(self.module, 'modtime', 0)
        self.descr=getattr(self.module, 'descr', "")

        #identifies the actions & tags linked to it
        self.tags=tags

        for name,val in list(tags.items()):
            self.actions[name]=eval("self.module.%s"%name)

    def installPackage(self,path):
        pass

############# custom install items

    def cleanSystem(self):
        print("clean platform")
        CMDS="""
pip uninstall JumpScale-core
# killall tmux  #dangerous
killall redis-server
rm -rf /usr/local/lib/python2.7/dist-packages/jumpscale*
rm -rf /usr/local/lib/python2.7/site-packages/jumpscale*
rm -rf /usr/local/lib/python2.7/dist-packages/JumpScale*
rm -rf /usr/local/lib/python2.7/site-packages/JumpScale*
rm -rf /usr/local/lib/python2.7/site-packages/JumpScale/
rm -rf /usr/local/lib/python2.7/site-packages/jumpscale/
rm -rf /usr/local/lib/python2.7/dist-packages/JumpScale/
rm -rf /usr/local/lib/python2.7/dist-packages/jumpscale/
rm /usr/local/bin/js*
rm /usr/local/bin/jpack*
rm /usr/local/bin/osis*
rm -rf /opt/sentry/
sudo stop redisac
sudo stop redisp
sudo stop redism
sudo stop redisc
killall redis-server
rm -rf /opt/redis/
"""
        self.executeCmds(CMDS,outputStdout=False, outputStderr=False,useShell = True,log=False,cwd=None,timeout=60,errors=[],ok=[],captureout=False,dieOnNonZeroExitCode=False)

    def prepareUbuntu14Development(self,js=False):
        self.cleanSystem()
        print("prepare ubuntu for development")

        CMDS="""
apt-get update
apt-get autoremove
apt-get -f install -y
apt-get upgrade -y
apt-get install mc python-git git ssh python2.7 python-requests python-apt openssl ca-certificates ipython -y
cd /tmp;wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
cd /tmp;python get-pip.py
apt-get install byobu tmux libmhash2 libpython-all-dev python-redis python-hiredis -y
        """
        self.executeCmds(CMDS)

        if js:
            self.installJS(clean=False)
        print("done")

    def prepareUbuntu14(self,js=False):
        self.cleanSystem()
        print("prepare ubuntu for development")

        CMDS="""
apt-get update
apt-get autoremove
apt-get -f install -y
apt-get upgrade -y
apt-get install mc git ssh python2.7 python-requests  -y
        """
        self.executeCmds(CMDS)

        if js:
            self.installJS(clean=False)
        print("done")

    def installDocker(self):
        if not do.exists(path="/usr/lib/apt/methods/https"):
            do.execute("apt-get install apt-transport-https -y")

        if not do.exists(path="/etc/apt/sources.list.d/docker.list"):
            do.execute("apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9",outputStdout=False, outputStderr=False,dieOnNonZeroExitCode=False)
            do.writeFile("/etc/apt/sources.list.d/docker.list","deb https://get.docker.com/ubuntu docker main\n")
            do.execute("apt-get update")
            do.execute("apt-get install lxc-docker -y",dieOnNonZeroExitCode=False)

    def gitConfig(self,name,email):
        self.execute("git config --global user.email \"%s\""%email)
        self.execute("git config --global user.name \"%s\""%name)      
        
    def replacesitecustomize(self):
        if not self.TYPE=="WIN":
            ppath="/usr/lib/python2.7/sitecustomize.py"
            if ppath.find(ppath):
                os.remove(ppath)
            self.symlink("%s/utils/sitecustomize.py"%self.BASE,ppath)
                
            def do(path,dirname,names):
                if path.find("sitecustomize")!=-1:
                    self.symlink("%s/utils/sitecustomize.py"%self.BASE,path)
            print("walk over /usr to find sitecustomize and link to new one")
            os.path.walk("/usr", do,"")
            os.path.walk("/etc", do,"")

    def _initExtra(self):
        """
        will get extra install tools lib
        """
        if not self._extratools:
            if not self.exists("ExtraTools.py"):
                url="https://raw.githubusercontent.com/Jumpscale/jumpscale_core/master/install/ExtraTools.py"
                self.download(url,"/tmp/ExtraTools.py")            
                if "/tmp" not in sys.path:
                    sys.path.append("/tmp")
            from ExtraTools import extra
            self.extra=extra
        self._extratools=True

    def getWalker(self):
        self._initExtra()
        return self.extra.getWalker(self)

do=InstallTools()


