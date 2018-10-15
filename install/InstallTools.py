try:
# from urllib3.request import urlopen
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

import os
import urlparse
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
import threading
from threading import Thread
import Queue
import os
import smtplib
import re

# from JumpScale import j



class InstallTools():
    def __init__(self,debug=False):

        self.TMP=tempfile.gettempdir().replace("\\","/")

        self._whoami=None

        if platform.system().lower()=="windows":
            self.TYPE="WIN"
            self.BASE="%s/"%os.environ["JSBASE"].replace("\\","/")

        elif sys.platform.startswith("darwin"):
            self.TYPE="OSX"
            self.BASE="/Users/Shared/jumpscale"
        elif sys.platform.startswith("linux"):
            self.BASE="/opt"
            self.TYPE=platform.linux_distribution(full_distribution_name=0)[0].upper()
            if self.TYPE!="UBUNTU":
                raise RuntimeError("Jumpscale only supports windows 7+, macosx, ubuntu 12+")
        else:
            raise RuntimeError("Jumpscale only supports windows 7+, macosx, ubuntu 12+")

        self.TYPE+=platform.architecture()[0][:2]

        if "JSBASE" in os.environ:
            self.BASE=os.environ["JSBASE"]

        if "CODEDIR" in os.environ:
            self.CODEDIR=os.environ["CODEDIR"]
        else:
            if self.TYPE.startswith("WIN"):
                raise RuntimeError("todo")
                self.CODEDIR="/opt/code"
            elif self.TYPE.startswith("OSX"):
                self.CODEDIR="/Users/Shared/code"
            else:
                self.CODEDIR="/opt/code"

        while self.BASE[-1]=="/":
            self.BASE=self.BASE[:-1]
        self.BASE+="/"

        #why was this needed ? (despiegk)
        # self.debug=False
        # self.createDir("%s/jumpscaleinstall"%(self.TMP))
        self.debug=debug

        self._extratools=False

        if str(sys.excepthook).find("apport_excepthook")!=-1:
            #if we get here it means is std python excepthook (I hope)
            # print ("OUR OWN EXCEPTHOOK")
            sys.excepthook = self.excepthook

        self._initSSH_ENV()


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

    def log(self,msg, level=None):
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

    def touch(self,path):
        self.writeFile(path,"")

    def textstrip(self,content,ignorecomments=False):
        #remove all spaces at beginning & end of line when relevant

        #find generic prepend for full file
        minchars=9999
        prechars = 0
        for line in content.split("\n"):
            if line.strip()=="":
                continue
            if ignorecomments:
                if line.startswith('#') and not line.startswith("#!"):
                    continue
            prechars=len(line)-len(line.lstrip())
            if prechars<minchars:
                minchars=prechars

        if prechars>0:
            #remove the prechars
            content="\n".join([line[minchars:] for line in content.split("\n")])

        return content

    def writeFile(self,path,content,strip=True):

        self.createDir(self.getDirName(path))

        if strip:
            content=self.textstrip(content,True)

        with open(path, "w") as fo:
            fo.write(content)

    def delete(self,path,force=False):

        self.removeSymlink(path)

        if path.strip().rstrip("/") in ["","/","/etc","/root","/usr","/opt","/usr/bin","/usr/sbin",self.CODEDIR]:
            raise RuntimeError('cannot delete protected dirs')

        # if not force and path.find(self.CODEDIR)!=-1:
        #     raise RuntimeError('cannot delete protected dirs')

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

    def copyTree(self, source, dest, keepsymlinks = False, deletefirst = False, overwriteFiles=True,ignoredir=[".egg-info",".dist-info"],ignorefiles=[".egg-info"],rsync=True,sshkey=None):
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
            if self.isDir(source):
                if dest[-1]!="/":
                    dest+="/"
                if source[-1]!="/":
                    source+="/"
                self.createDir(dest)
            cmd="rsync "
            if sshkey:
                cmd += "-e 'ssh -i %s'" % sshkey
            cmd+=" -a --no-compress --max-delete=0 %s %s %s"%(excl,source,dest)
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

    def copyFile(self,source,dest,deletefirst=False,skipIfExists=False):
        """
        """
        if self.isDir(dest):
            dest=self.joinPaths(dest,self.getBaseName(source))

        if skipIfExists:
            if self.exists(dest):
                return

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
            self.removeSymlink(dest)

        if delete:
            if self.TYPE=="WIN":
                self.removeSymlink(dest)
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
            if not self.exists(dest):
                os.symlink(src,dest)

    def symlinkFilesInDir(self,src,dest,delete=True, includeDirs=False):
        if includeDirs:
            items = self.listFilesAndDirsInDir(src, recursive=False,followSymlinks=False,listSymlinks=False)
        else:
            items = self.listFilesInDir(src, recursive=False,followSymlinks=True,listSymlinks=True)
        for item in items:
            dest2="%s/%s"%(dest,self.getBaseName(item))
            dest2=dest2.replace("//","/")
            print(("link %s:%s"%(item,dest2)))
            self.symlink(item,dest2,delete=delete)

    def removeSymlink(self,path):
        if self.TYPE=="WIN":
            try:
                cmd="junction -d %s 2>&1 > null" % (path)
                print(cmd)
                os.system(cmd)
            except Exception as e:
                pass
        else:
            if self.isLink(path):
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

    def chdir(self,ddir=""):
        """
        if ddir=="" then will go to tmpdir
        """
        if ddir=="":
            ddir=self.TMP
        os.chdir(ddir)

    #########NON FS

    def download(self,url,to="",overwrite=True,retry=3,timeout=0,login="",passwd="",minspeed=0,multithread=False,curl=False):
        """
        @return path of downloaded file
        @param minspeed is kbytes per sec e.g. 50, if less than 50 kbytes during 10 min it will restart the download (curl only)
        @param when multithread True then will use aria2 download tool to get multiple threads
        """
        def download(url,to,retry=3):
            if timeout==0:
                handle = urlopen(url)
            else:
                handle = urlopen(url,timeout=timeout)
            nr=0
            while nr < retry+1:
                try:
                    with open(to, 'wb') as out:
                        while True:
                            data = handle.read(1024)
                            if len(data) == 0: break
                            out.write(data)
                    handle.close()
                    out.close()
                    return
                except Exception,e:
                    print "DOWNLOAD ERROR:%s\n%s"%(url,e)
                    try:
                        handle.close()
                    except:
                        pass
                    try:
                        out.close()
                    except:
                        pass
                    handle = urlopen(url)
                    nr+=1


        # os.chdir(self.TMP)
        print(('Downloading %s ' % (url)))
        if to=="":
            to=self.TMP+"/"+url.replace("\\","/").split("/")[-1]

        if overwrite:
            if self.exists(to):
                self.delete(to)
                self.delete("%s.downloadok"%to)
        else:
            if self.exists(to) and self.exists("%s.downloadok"%to):
                # print "NO NEED TO DOWNLOAD WAS DONE ALREADY"
                return to

        self.createDir(self.getDirName(to))

        if curl and self.checkInstalled("curl"):
            minspeed=0
            if minspeed!=0:
                minsp="-y %s -Y 600"%(minspeed*1024)
            else:
                minsp=""
            if login:
                user="--user %s:%s "%(login,passwd)
            else:
                user=""

            cmd = "curl '%s' -o '%s' %s %s --connect-timeout 5 --retry %s --retry-max-time %s"%(url,to,user,minsp,retry,timeout)
            if self.exists(to):
                cmd += " -C -"
            print cmd
            self.delete("%s.downloadok"%to)
            rc, out, err = self.execute(cmd, dieOnNonZeroExitCode=False)
            if rc == 33: # resume is not support try again withouth resume
                self.delete(to)
                cmd = "curl '%s' -o '%s' %s %s --connect-timeout 5 --retry %s --retry-max-time %s"%(url,to,user,minsp,retry,timeout)
                rc, out, err = self.execute(cmd, dieOnNonZeroExitCode=False)
            if rc > 0:
                raise RuntimeError("Could not download:{}.\nErrorcode: {} Error:\n {}".format(url, rc, err))
            else:
                self.touch("%s.downloadok"%to)
        elif multithread:
            raise RuntimeError("not implemented yet")
        else:
            download(url,to,retry)
            self.touch("%s.downloadok"%to)

        return to

    def isUnix(self):
        if sys.platform.lower().find("linux")!=-1:
            return True
        return False

    def isWindows(self):
        if sys.platform.startswith("win")==1:
            return True
        return False

    def executeBashScript(self,content,path=None,die=True):
        if die:
            content="set -ex\n%s"%content
        if path!=None:
            content="cd %s\n%s"%content
            path2=self.joinPaths(path,"do.sh")
        else:
            path2=self.getTmpPath("do.sh")
        self.writeFile(path2,content,strip=True)
        return self.execute("sh %s"%path2,die=die)

    def executeCmds(self,cmdstr, outputStdout=True, outputStderr=True,useShell = True,log=True,cwd=None,timeout=120,errors=[],ok=[],captureout=True,dieOnNonZeroExitCode=True):
        rc_=""
        out_=""
        err_=""
        for cmd in cmdstr.split("\n"):
            if cmd.strip()=="" or cmd[0]=="#":
                continue
            cmd=cmd.strip()
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

    def execute(self, command , outputStdout=True, outputStderr=True, useShell=True, log=True, cwd=None, timeout=0, errors=[], ok=[], captureout=True, dieOnNonZeroExitCode=True):
        """
        @param errors is array of statements if found then exit as error
        return rc,out,err
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

        env = os.environ.copy()
        if 'LD_LIBRARY_PATH' in env:
            binpath = os.path.join(env['LD_LIBRARY_PATH'], command)
            if not self.isFile(binpath) and env['LD_LIBRARY_PATH'] not in command:
                env.pop('LD_LIBRARY_PATH')

        p=Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=ON_POSIX, \
                    shell=useShell, env=env, universal_newlines=True,cwd=cwd,bufsize=0,**popenargs)

        class StreamReader(threading.Thread):
            def __init__(self, stream, queue, flag):
                super(StreamReader, self).__init__()
                self.stream = stream
                self.queue = queue
                self.flag = flag
                self._stopped = False
                self.setDaemon(True)

            def run(self):
                while not self.stream.closed and not self._stopped:
                    buf = ''
                    buf = self.stream.readline()
                    if len(buf)>0:
                        self.queue.put((self.flag, buf))
                    else:
                        break
                self.queue.put(('T', self.flag))

        serr = p.stderr
        sout = p.stdout
        inp = Queue.Queue()

        outReader = StreamReader(sout, inp, 'O')
        errReader = StreamReader(serr, inp, 'E')

        outReader.start()
        errReader.start()

        start=time.time()

        err=""
        out=""
        rc=1000

        out_eof = False
        err_eof = False

        while not out_eof or not err_eof:
            # App still working
            try:
                chan,line = inp.get(block=True, timeout = 1.0)
                #print chan, line
                if chan == 'T':
                    if line == 'O':
                        out_eof = True
                    elif line == 'E':
                        err_eof = True
                    continue

                if ok<>[]:
                    for item in ok:
                        if line.find(item)!=-1:
                            rc=0
                            break
                if errors<>[]:
                    for item in errors:
                        if line.find(item)!=-1:
                            rc=997
                            break
                    if rc==997 or rc==0:
                        break

                if chan=='O':
                    if outputStdout:
                        print (line.strip())
                    if captureout:
                        out+=line
                elif chan=='E':
                    if outputStderr:
                        print ("E:%s"%line.strip())
                    if captureout:
                        err+=line

            except Queue.Empty:
                pass
            if timeout>0:
                if time.time()>start+timeout:
                    print "TIMEOUT"
                    rc=999
                    p.kill()
                    p.wait()

                    break

        if rc<>999:
            outReader.join()
            errReader.join()
            p.wait()
        if rc==1000:
            rc = p.returncode


        if rc>0 and dieOnNonZeroExitCode:
            if err<>"":
                raise RuntimeError("Could not execute cmd:\n'%s'\nerr:\n%s"%(command,err))
            else:
                raise RuntimeError("Could not execute cmd:\n'%s'\nout:\n%s"%(command,out))

        return rc,out,err

    def executeInteractive(self,command):
        exitcode = os.system(command)
        return exitcode

    def downloadExpandTarGz(self,url,destdir,deleteDestFirst=True,deleteSourceAfter=True):
        print((self.getBaseName(url)))
        tmppath=self.getTmpPath(self.getBaseName(url))
        self.download(url,tmppath)
        self.expandTarGz(tmppath,destdir)

    def expandTarGz(self,path,destdir,deleteDestFirst=True,deleteSourceAfter=False):
        import gzip

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



    def rewriteGitRepoUrl(self, url="", login=None, passwd=None, protocol=None):
        """
        Rewrite the url of a git repo with login and passwd if specified

        Args:
            url (str): the HTTP URL of the Git repository. ex: 'https://github.com/odoo/odoo'
            login (str): authentication login name
            passwd (str): authentication login password
            protocol (str): rewrite url to either https or ssh

        Returns:
            (repository_host, repository_type, repository_account, repository_name, repository_url)
        """
        parseresult = urlparse.urlparse(url)
        if not parseresult:
            raise RuntimeError("Url is invalid. Must be in the form of 'http(s)://hostname/account/repo'")
        if protocol and protocol not in ['ssh', 'https']:
            raise RuntimeError("protocol must be either https or ssh")
        pathparts = parseresult.path.strip('/').split('/')
        login = protocol if not login and protocol == 'ssh' else login
        if len(pathparts) != 2:
            raise RuntimeError("Url is invalid. Must be in the form of 'http(s)://hostname/account/repo'")
        if parseresult.path == url:
            # this is git/ssh url
            if protocol is None:
                login = 'ssh'
                protocol = 'ssh'
            userandhost, path = parseresult.path.split(':')
            repository_account, repository_name = path.split('/')
            repository_host = userandhost.split('@')[-1]
        else:
            if protocol is None:
                protocol = parseresult.scheme
            repository_host = parseresult.hostname
            if parseresult.port:
                repository_host += ":{}".format(parseresult.port)
            repository_account, repository_name = pathparts
            if not login:
                login = parseresult.username
            if not passwd:
                passwd = parseresult.password

        if not repository_name.endswith('.git'):
            repository_name += '.git'

        if login == 'ssh':
            repository_url = 'git@%(host)s:%(account)s/%(name)s'
        elif login and login != 'guest':
            if passwd:
                repository_url = '%(protocol)s://%(login)s:%(password)s@%(host)s/%(account)s/%(repo)s'
            else:
                repository_url = '%(protocol)s://%(login)s@%(host)s/%(account)s/%(repo)s'

        else:
            repository_url = '%(protocol)s://%(host)s/%(account)s/%(repo)s'
        repository_url = repository_url % {
                'protocol': protocol,
                'login': login,
                'password': passwd,
                'host': repository_host,
                'name': repository_name,
                'account': repository_account,
                'repo': repository_name,
            }
        return protocol, repository_host, repository_account, repository_name, repository_url

    def parseGitConfig(self,repopath):
        """
        @param repopath is root path of git repo
        @return (giturl,account,reponame,branch,login,passwd)
        login will be ssh if ssh is used
        login & passwd is only for https
        """
        path=j.system.fs.joinPaths(dest,".git","config")
        if not j.system.fs.exists(path=path):
            j.events.inputerror_critical("cannot find %s"%path)
        config=j.system.fs.fileGetContents(path)
        state="start"
        for line in config.split("\n"):
            line2=line.lower().strip()
            if state=="remote":
                if line.startswith("url"):
                    url=line.split("=",1)[1]
                    url=url.strip().strip("\"").strip()
            if line2.find("[remote")!=-1:
                state="remote"
            if line2.find("[branch"):
                branch=line.split(" \"")[1].strip("]\" ").strip("]\" ").strip("]\" ")

    def whoami(self):
        if self._whoami!=None:
            return self._whoami
        rc,result,err=self.execute("whoami",dieOnNonZeroExitCode=False,outputStdout=False, outputStderr=False)
        if rc>0:
            #could not start ssh-agent
            raise RuntimeError("Could not call whoami,\nstdout:%s\nstderr:%s\n"%(result,err))
        else:
            self._whoami=result.strip()
        return self._whoami

    def addSSHAgentToBashrc(self,path=None):
        if path==None:
            if "root"==self.whoami():
                self.addSSHAgentToBashrc(path="/root/.bashrc")
            path=self.joinPaths(os.environ["HOME"],".bashrc")
            self.addSSHAgentToBashrc(path=path)
        else:
            content=self.readFile(path)
            out=""
            for line in content.split("\n"):
                if line.find("#JSSSHAGENT")!=-1:
                    continue
                if line.find("SSH_AUTH_SOCK")!=-1:
                    continue

                out+="%s\n"%line

            out+="\njs 'j.do.loadSSHAgent()' #JSSSHAGENT\n"
            socketpath="%s/sshagent_socket"%path.replace("/.bashrc","")
            out+="export SSH_AUTH_SOCK=%s \n"%socketpath
            out=out.replace("\n\n\n","\n\n")
            out=out.replace("\n\n\n","\n\n")
            self.writeFile(path,out)

    def _initSSH_ENV(self,force=False):
        if force or not os.environ.has_key("SSH_AUTH_SOCK"):
            socketpath = self._getSSHSocketpath()
            if socketpath:
                os.putenv("SSH_AUTH_SOCK", socketpath)
                os.environ["SSH_AUTH_SOCK"] = socketpath

    def _getSSHSocketpath(self):
        socketpath = "%s/sshagent_socket"%os.environ.get('HOME')
        if self.exists(socketpath):
            return socketpath
        return None

    def loadSSHKeys(self,path=None):
        """
        @param loadedkeys this is to win time, it represents the already loaded keys
        """

        if path!=None:
            #specific path so load
            self._initSSH_ENV()
            #timeout after 10 h
            rc,result,err=self.execute("ssh-add %s -t 36000"%path,dieOnNonZeroExitCode=False,outputStdout=False, outputStderr=False)
            # if rc>0:
            #     raise RuntimeError("Could not add key to sshagent, something went wrong,\nstdout:%s\nstderr:%s\n"%(result,err))
        else:
            #no path specified need to find key paths
            if "root"==self.whoami():
                self.listFilesInDir(self.joinPaths(os.environ["HOME"],".ssh"),filter="*.pub")
                for keypath in self.listFilesInDir("/root/.ssh",filter="*.pub"):
                    self.loadSSHKeys(path=keypath[:-4])

            for keypath in self.listFilesInDir(self.joinPaths(os.environ["HOME"],".ssh"),filter="*.pub"):
                self.loadSSHKeys(path=keypath[:-4])

    def authorizeSSHKey(self,remoteipaddr,login="root",remoteuser="root",passwd=None,keypathpub=None,sshport=22):
        """
        if keypath==None then it defaults to "~/.ssh/id_rsa"
        """
        # cmd="scp %s %s@%s:~/%s"%(keypath,login,remoteipaddr,j.system.fs.getBaseName(keypath))
        # j.do.executeInteractive(cmd)


        import paramiko
        paramiko.util.log_to_file("/tmp/paramiko.log")
        ssh = paramiko.SSHClient()

        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print "ssh connect:%s %s"%(remoteipaddr,login)
        # from fabric.api import env
        # env.no_keys = True
        ssh.connect(remoteipaddr, username=login, password=passwd, allow_agent=False,look_for_keys=False)
        print "ok"

        if keypathpub==None:
            if login!="root":
                keypathpub="/home/%s/.ssh/id_rsa"%login
            else:
                keypathpub="/root/.ssh/id_rsa"


        ftp=ssh.open_sftp()
        if remoteuser=="root":
            authkeypath="/root/.ssh/authorized_keys"
        else:
            authkeypath="/home/%s/.ssh/authorized_keys"%(remoteLogin)

        if not self.exists(keypathpub):
            raise RuntimeError("Cannot find keypath:%s"%keypathpub)

        if login!="root":
            basename=self.getBaseName(keypathpub)
            tmpfile="/home/%s/.ssh/%s"%(login,basename)
            print "push key to /home/%s/.ssh/%s"%(login,basename)
            ftp.put(keypathpub,tmpfile)

            #cannot upload directly to root dir
            cmd="ssh %s@%s 'cat %s | sudo tee -a %s '"%(login,remoteipaddr,tmpfile,authkeypath)
            print "do the following on the console\nsudo -s\ncat %s >> %s"%(tmpfile,authkeypath)
            print cmd
            self.executeInteractive(cmd)

        else:
            ftp.get(authkeypath,"%s/authorized_keys"%self.TMP)
            self.readFile("%s/authorized_keys"%self.TMP)
            from IPython import embed
            print "DEBUG NOW authorizeSSHKey on j.do"
            embed()


    def loadSSHAgent(self,path=None,createkeys=False,keyname="id_rsa"):
        """
        check if ssh-agent is available & there is key loaded

        @param path: is path to private ssh key

        the primary key is 'id_rsa' and will be used as default e.g. if authorizing another node then this key will be used

        """
        if path==None:
            path2=self.joinPaths(os.environ["HOME"],".ssh",keyname)
            if not self.exists(path2):
                if createkeys:
                    self.executeInteractive("ssh-keygen -t rsa -b 4096 -f %s"%path2)
                    return self.loadSSHAgent(path=path2,createkeys=False)
        else:
            if not self.exists(path):
                raise RuntimeError("Cannot find ssh key on %s"%path)
        #key is now in path
        #1 lets try if we can get ssh-agent and if we should start
        socketpath=self._getSSHSocketpath()
        if not self.exists(socketpath):
            #ssh-agent not loaded
            rc,result,err=self.execute("ssh-agent -a %s"%socketpath,dieOnNonZeroExitCode=False,outputStdout=False, outputStderr=False)
            if rc>0:
                #could not start ssh-agent
                raise RuntimeError("Could not start ssh-agent, something went wrong,\nstdout:%s\nstderr:%s\n"%(result,err))
            else:
                #get pid from result of ssh-agent being started
                if not self.exists(socketpath):
                    raise RuntimeError("Serious bug, ssh-agent not started while there was no error, should never get here")
                pid=int([item for item in result.split("\n") if item.find("pid")!=-1][-1].split(" ")[-1].strip("; "))
                self.writeFile(self.joinPaths(self.TMP,"ssh-agent-pid"),str(pid))
                self.addSSHAgentToBashrc()
                return self.loadSSHAgent(path=path,createkeys=createkeys)
        else:
            #ssh agent should be loaded because ssh-agent socket has been found
            # pid=int(self.readFile(self.joinPaths(self.TMP,"ssh-agent-pid")))
            self._initSSH_ENV(True)
            rc,result,err=self.execute("ssh-add -l",dieOnNonZeroExitCode=False,outputStdout=False, outputStderr=False)
            if rc==2:#>0 and err.find("not open a connection")!=-1:
                #no ssh-agent found
                raise RuntimeError("Could not connect to ssh-agent, this is bug, ssh-agent should be loaded by now")
            elif rc==1:
                #no keys but agent loaded
                result=""
            elif rc>0:
                raise RuntimeError("Could not start ssh-agent, something went wrong,\nstdout:%s\nstderr:%s\n"%(result,err))

        self.loadSSHKeys(path=path)



    # def checkSSHAgentAvailable(self):


    #     if rc==0:
    #         #sshagent is loaded
    #         pass


    #     from IPython import embed
    #     print "DEBUG NOW checkSSHAgentKeyAvailable"
    #     embed()
    #     p


    #     errormsg="Could not find SSH agent, please start by 'eval \"$(ssh-agent -s)\"' before running this cmd,\nand make sure appropriate keys are added with ssh-add ..."
    #     sshkeypubcontent=" ".join(sshkeypub.split(" ")[1:]).strip().split("==")[0]+"=="
    #     #check if current priv key is in ssh-agent
    #     agent=paramiko.agent.Agent()
    #     try:
    #         keys=agent.get_keys()
    #     except Exception,e:
    #         j.events.opserror_critical( errormsg)

    #     if keys==():
    #         j.events.opserror_critical( errormsg)

    #     for key in keys:
    #         if key.get_base64()==sshkeypubcontent:
    #             return True
    #     return False

    def getGitRepoArgs(self, url="", dest=None, login=None, passwd=None, reset=False,branch=None):
        """
        Extracts and returns data useful in cloning a Git repository.

        Args:
            url (str): the HTTP/GIT URL of the Git repository to clone from. eg: 'https://github.com/odoo/odoo.git'
            dest (str): the local filesystem path to clone to
            login (str): authentication login name (only for http)
            passwd (str): authentication login password (only for http)
            reset (boolean): if True, any cached clone of the Git repository will be removed
            branch (str): branch to be used

        #### Process for finding authentication credentials:

        - first check there is an ssh-agent and there is a key attached to it, if yes then no login & passwd will be used & method will always be git
        - if not ssh found (we ONLY support by means of ssh-agent)
            - then we will check if url is github & ENV argument GITHUBUSER & GITHUBPASSWD is set
                - if env arguments set, we will use those & ignore login/passwd arguments
            - we will check if login/passwd specified in URL, if yes willl use those (so they get priority on login/passwd arguments)
            - we will see if login/passwd specified as arguments, if yes will use those
        - if we don't know login or passwd yet then
            - login/passwd will be fetched from local git repo directory (if it exists and reset==False)
        - if at this point still no login/passwd then we will try to checkout with anonymous


        #### Process for defining branch

        - if branch arg: None
            - check if git directory exists if yes take that branch
            - default to 'master'
        - if it exists, use the branch arg

        Returns:
            (repository_host, repository_type, repository_account, repository_name,branch, login, passwd)

            - repository_type http or git

        Remark:
            url can be empty, then the git params will be fetched out of the git configuration at that path
        """

        if url=="":
            if not j.system.fs.exists(path=dest):
                j.events.inputerror_critical("Could not find git repo path:%s, url was not specified so git destination needs to be specified."%(dest))



        if login==None and url.find("github.com/")!=-1:
            #can see if there if login & passwd in OS env
            #if yes fill it in
            if os.environ.has_key("GITHUBUSER"):
                login=os.environ["GITHUBUSER"]
            if os.environ.has_key("GITHUBPASSWD"):
                passwd=os.environ["GITHUBPASSWD"]

        protocol, repository_host, repository_account, repository_name, repository_url = self.rewriteGitRepoUrl(url=url,login=login,passwd=passwd)

        repository_type = repository_host.split('.')[0] if '.' in repository_host else repository_host

        # strip username/password on type if exists
        if "@" in repository_type and ":"in  repository_type:
            repository_type = repository_type.rsplit('@', 1)[1]

        if not dest:
            dest = '%(codedir)s/%(type)s/%(account)s/%(repo_name)s' % {
                'codedir': self.CODEDIR,
                'type': repository_type.lower(),
                'account': repository_account,
                'repo_name': repository_name[:-4].lower(),  # Remove the trailling '.git'
            }

            # warning: workaround for jumpscale setup
            # needt to be fixed, but no idea how
            if not self.isDir(dest):
                newdest = '%(codedir)s/%(type)s/%(account)s/%(repo_name)s' % {
                    'codedir': self.CODEDIR,
                    'type': repository_type.lower(),
                    'account': repository_account.lower(),
                    'repo_name': repository_name[:-4].lower(),  # Remove the trailling '.git'
                }

                if self.isDir(newdest) or repository_account.lower() == "jumpscale":
                    dest = newdest

        if reset:
            self.delete(dest)

        self.createDir(dest)

        return repository_host, repository_type, repository_account, repository_name, dest, repository_url

    def pullGitRepo(self,url="",dest=None,login=None,passwd=None,depth=1,ignorelocalchanges=False,reset=False,branch=None,revision=None,tag=None,offline=False):
        """
        will clone or update repo
        if dest == None then clone underneath: /opt/code/$type/$account/$repo
        will ignore changes !!!!!!!!!!!
        """

        base,provider,account,repo,dest,url=self.getGitRepoArgs(url,dest,login,passwd,reset=reset)

        if dest==None and branch==None:
            branch="master"

        checkdir="%s/.git"%(dest)
        rev = revision or branch or tag or 'HEAD'
        if self.exists(checkdir):
            if offline:
                return dest
            elif ignorelocalchanges:
                print(("git pull, ignore changes %s -> %s"%(url,dest)))
                cmd="cd %s;git fetch -f -u"%dest
                if depth!=None:
                    cmd+=" --depth %s"%depth
                if tag is not None:
                    cmd+=" origin tag %s" % tag
                if branch is not None:
                    self.execute("cd %s; git remote set-branches origin '*'" % dest)
                    cmd+=" origin %s" % branch
                self.execute(cmd)
                if branch is not None:
                    self.execute("cd {0}; git checkout -B {1} remotes/origin/{1}".format(dest, branch))
                else:
                    self.execute("cd %s;git reset --hard %s"%(dest, rev),timeout=600)
            else:
                #pull
                print(("git pull %s -> %s"%(url,dest)))
                if branch!=None:
                    cmd="cd %s;git pull origin %s"%(dest,branch)
                elif tag is not None:
                    cmd="cd %s;git pull origin tag %s"%(dest,tag)
                else:
                    cmd="cd %s;git pull"%dest
                self.execute(cmd,timeout=600)
        else:
            if offline:
                raise RuntimeError("Cannot clone repo %s to location %s\nYou can either disable offline mode or manually clone the repo"%(url,dest))
            print(("git clone %s -> %s"%(url,dest)))
            extra = ""
            if depth and depth != 0:
                 extra = "--depth=%s" % depth
            if branch or tag:
                cmd="cd %s;git clone %s --single-branch -b %s %s %s"%(self.getParent(dest),extra, tag or branch,url,dest)
            else:
                cmd="cd %s;git clone %s  %s %s"%(self.getParent(dest),extra,url,dest)
            print cmd

            if depth!=None:
                cmd+=" --depth %s"%depth
            self.execute(cmd,timeout=600)

        if not ignorelocalchanges:
            cmd="cd %s; git checkout %s || (git fetch origin %s:%s && git checkout %s)" % (dest, rev, rev, rev, rev)
            print cmd
            self.execute(cmd,timeout=600)

        return dest

    def checkInstalled(self,cmdname):
        """
        @param cmdname is cmd to check e.g. curl
        """
        res = self.execute("which %s" % cmdname, False)
        if res[0] == 0:
            return True
        else:
            return False

    def getGitReposListLocal(self,provider="",account="",name="",errorIfNone=True):
        repos={}
        if self.exists(self.CODEDIR):
            for top in self.listDirsInDir(self.CODEDIR, recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
                if provider!="" and provider!=top:
                    continue
                for accountfound in self.listDirsInDir("%s/%s"%(self.CODEDIR,top), recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
                    if account!="" and account!=accountfound:
                        continue
                    accountfounddir="/%s/%s/%s"%(self.CODEDIR,top,accountfound)
                    for reponame in self.listDirsInDir("%s/%s/%s"%(self.CODEDIR,top,accountfound), recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
                        if name!="" and name!=reponame:
                            continue
                        repodir="%s/%s/%s/%s"%(self.CODEDIR,top,accountfound,reponame)
                        if self.exists(path="%s/.git"%repodir):
                            repos[reponame]=repodir
        if len(list(repos.keys()))==0 and errorIfNone:
            raise RuntimeError("Cannot find git repo '%s':'%s':'%s'"%(provider,account,name))
        return repos

    def pushGitRepos(self,message,name="",update=True,provider="",account=""):
        """
        if name specified then will look under code dir if repo with path can be found
        if not or more than 1 there will be error
        @param provider e.g. git, github
        """
        #@todo make sure we use gitlab or github account if properly filled in
        repos=self.getGitReposListLocal(provider,account,name)
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

    def updateGitRepos(self,provider="",account="",name="",message=""):
        repos=self.getGitReposListLocal(provider,account,name)
        for name,path in list(repos.items()):
            print(("push git repo:%s"%path))
            cmd="cd %s;git add . -A"%(path)
            self.executeInteractive(cmd)
            cmd="cd %s;git commit -m \"%s\""%(path,message)
            self.executeInteractive(cmd)
            cmd="cd %s;git pull"%(path)
            self.executeInteractive(cmd)

    def changeLoginPasswdGitRepos(self,provider,login,passwd):
        """
        walk over all git repo's found in account & change login/passwd
        """
        for reponame,repopath in list(self.getGitReposListLocal(provider).items()):
            import re
            configpath="%s/.git/config"%repopath
            text=self.readFile(configpath)
            text2=text
            for item in re.findall(re.compile(r'//.*@%s'%provider), text):
                newitem="//%s:%s@%s"%(login,passwd,provider)
                text2=text.replace(item,newitem)
            if text2!=text:
                print(("changed login/passwd on %s"%configpath))
                self.writeFile(configpath,text2)

    def _initExtra(self):
        """
        will get extra install tools lib
        """
        if not self._extratools:
            if not self.exists("ExtraTools.py"):
                url="https://raw.githubusercontent.com/jumpscale7/jumpscale_core/master/install/ExtraTools.py"
                self.download(url,"/tmp/ExtraTools.py")
                if "/tmp" not in sys.path:
                    sys.path.append("/tmp")
            from ExtraTools import extra
            self.extra=extra
        self._extratools=True

    def getInstallCommand(self):
        from JumpScale import j

        branches = {
            'jsbranch': j.clients.git.get('/opt/code/github/jumpscale7/jumpscale_core7').getBranchOrTag()[1],
            'aysbranch': j.clients.git.get('/opt/code/github/jumpscale7/ays_jumpscale7').getBranchOrTag()[1]
        }

        return 'export JSBRANCH="%(jsbranch)s"; export AYSBRANCH="%(aysbranch)s"; curl https://raw.githubusercontent.com/jumpscale7/jumpscale_core7/%(jsbranch)s/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh' % branches


    def getWalker(self):
        self._initExtra()
        return self.extra.getWalker(self)

    def loadScript(self,path):
        print(("load jumpscript: %s"%path))
        source = self.readFile(path)
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

do=InstallTools()

class Installer():

    def installJS(self,base="",clean=False,insystem=True,GITHUBUSER="",GITHUBPASSWD="",CODEDIR="",JSGIT="https://github.com/jumpscale7/jumpscale_core7.git",JSBRANCH="master",AYSGIT="https://github.com/jumpscale7/ays_jumpscale7",AYSBRANCH="master",SANDBOX=1,EMAIL="",FULLNAME="",offline=False):
        """
        @param pythonversion is 2 or 3 (3 no longer tested and prob does not work)
        if 3 and base not specified then base becomes /opt/jumpscale73

        @param insystem means use system packaging system to deploy dependencies like python & python packages
        @param codedir is the location where the code will be installed, code which get's checked out from github
        @param base is location of root of JumpScale
        @copybinary means copy the binary files (in sandboxed mode) to the location, don't link

        JSGIT & AYSGIT allow us to chose other install sources for jumpscale as well as AtYourService repo

        IMPORTANT: if env var's are set they get priority

        """

        #everything else is dangerous now
        copybinary=True

        tmpdir=do.TMP

        if os.environ.has_key("JSBRANCH"):
            JSBRANCH=os.environ["JSBRANCH"]

        if base!="":
            os.environ["JSBASE"]=base

        if not os.environ.has_key("JSBASE"):

            if sys.platform.startswith('win'):
                raise RuntimeError("Cannot find JSBASE, needs to be set as env var")
            elif sys.platform.startswith('darwin'):
                os.environ["JSBASE"]="/Users/Shared/jumpscale/"
            else:
                #for all linux versions
                os.environ["JSBASE"]="/opt/jumpscale7"

        # if pythonversion==3:
        #     os.environ["JSBASE"]+="3"            #add nr 3 to path when python 3

        base=os.environ["JSBASE"]

        if CODEDIR=="":
            if sys.platform.startswith('win'):
                raise RuntimeError("Cannot find JSBASE, needs to be set as env var")
            elif sys.platform.startswith('darwin'):
                CODEDIR="/Users/Shared/code"
            else:
                #for all linux versions
                CODEDIR="/opt/code"

        print(("Install Jumpscale in %s"%base))

        #this means if env var's are set they get priority
        args=["GITHUBUSER","GITHUBPASSWD","JSGIT","JSBRANCH","AYSGIT","AYSBRANCH","CODEDIR","SANDBOX","EMAIL","FULLNAME"]
        #walk over all var's & set defaults or get them from env
        for var in args:
            if os.environ.has_key(var):
                exec("%s = os.environ[\"%s\"]"%(var,var))

        if do.TYPE!=("UBUNTU64"):
            SANDBOX=0

        os.environ["GITHUBUSER"]=GITHUBUSER
        os.environ["GITHUBPASSWD"]=GITHUBPASSWD
        os.environ["JSGIT"]=JSGIT
        os.environ["JSBRANCH"]=JSBRANCH
        os.environ["AYSGIT"]=AYSGIT
        os.environ["AYSBRANCH"]=AYSBRANCH
        os.environ["CODEDIR"]=CODEDIR
        os.environ["SANDBOX"]=str(SANDBOX)

        if EMAIL!="":
            self.gitConfig(FULLNAME,EMAIL)

        if clean:
            self.cleanSystem()

        self.debug=True

        self.prepare(SANDBOX=SANDBOX,base=base,offline=offline)

        print ("pull core")
        do.pullGitRepo(JSGIT,branch=JSBRANCH, depth=1,offline=offline)
        src="%s/github/jumpscale7/jumpscale_core7/lib/JumpScale"%do.CODEDIR
        self.debug=False

        if do.TYPE.startswith("OSX"):
            destjs="/usr/local/lib/python2.7/site-packages/JumpScale"
        elif do.TYPE.startswith("WIN"):
            raise RuntimeError("do")
        else:
            destjs="/usr/local/lib/python2.7/dist-packages/JumpScale"
            do.delete(destjs)
            do.createDir(destjs)

        # if pythonversion==2:
        #     dest="/usr/local/lib/python2.7/dist-packages/JumpScale"
        # else:
        #     dest="/usr/local/lib/python3.4/dist-packages/JumpScale"


        do.createDir("%s/lib"%base)
        do.createDir("%s/bin"%base)
        do.createDir("%s/hrd/system"%base)
        do.createDir("%s/hrd/apps"%base)

        dest="%s/lib/JumpScale"%base
        do.createDir(dest)
        do.symlinkFilesInDir(src, dest, includeDirs=True)
        do.symlinkFilesInDir(src, destjs, includeDirs=True)

        for item in ["InstallTools","ExtraTools"]:
            src="%s/github/jumpscale7/jumpscale_core7/install/%s.py"%(do.CODEDIR,item)
            dest2="%s/%s.py"%(dest,item)
            do.symlink(src, dest2)
            dest2="%s/%s.py"%(destjs,item)
            do.symlink(src, dest2)

        src="%s/github/jumpscale7/jumpscale_core7/shellcmds"%do.CODEDIR
        desttest="/usr/local/bin/js"
        if insystem or not self.exists(desttest):
            dest="/usr/local/bin"
            do.symlinkFilesInDir(src, dest)

        dest="%s/bin"%base
        do.symlinkFilesInDir(src, dest)



        #it was not logical that the behaviour in the /usr/local was different than the one in the sandbox
        # if insystem or not self.exists(destjs):

        #     dest="%s/lib/JumpScale/"%(base)
        #     do.copyTree(src,destjs)

        self._writeenv(basedir=base,insystem=insystem,SANDBOX=SANDBOX,CODEDIR=CODEDIR)

        if not insystem:
            sys.path=[]
        sys.path.insert(0,"%s/lib"%base)

        from JumpScale import j

        #make sure all configured paths are created
        for item in j.application.config["system"]["paths"].values():
            do.createDir(item)

        if do.TYPE == "UBUNTU64":
            j.system.platform.ubuntu.serviceEnableStartAtBoot("ays")

        print("Get atYourService metadata.")
        do.pullGitRepo(AYSGIT, branch=AYSBRANCH, depth=1,offline=offline)

        print ("install was successfull")
        # if pythonversion==2:
        print ("to use do 'js'")

    def _writeenv(self,basedir,insystem=True,SANDBOX=1,CODEDIR=""):

        if CODEDIR=="":
            CODEDIR=self.CODEDIR

        do.createDir("%s/hrd/system/"%basedir)
        do.createDir("%s/hrd/apps/"%basedir)

        C="""
        paths.base=$base
        paths.bin=$(paths.base)/bin
        paths.code=$CODEDIR
        paths.lib=$(paths.base)/lib

        paths.jsLib=$(paths.lib)/JumpScale
        paths.libExt=$(paths.base)/libext
        paths.app=$(paths.base)/apps
        paths.var=$(paths.base)/var
        paths.log=$(paths.var)/log
        paths.pid=$(paths.var)/pid

        paths.cfg=$(paths.base)/cfg
        paths.hrd=$(paths.base)/hrd

        system.logging = 1
        system.sandbox = $sandbox

        """
        C=C.replace("$base",basedir.rstrip("/"))
        C=C.replace("$sandbox",str(SANDBOX))
        C=C.replace("$CODEDIR",CODEDIR)

        do.writeFile("%s/hrd/system/system.hrd"%basedir,C)

        #         C="""
        # email                   = @ASK descr:'email as used for github'
        # fullname                = @ASK descr:'full name as used for github'
        # git.login               = @ASK descr:'login for github'
        # git.passwd              = @ASK descr:'passwd for github'
        # """

        C="""
        email                   = {EMAIL}
        fullname                = {FULLNAME}
        git.login               = {GITHUBUSER}
        git.passwd              = {GITHUBPASSWD}
        """

        for item in ["EMAIL","FULLNAME","GITHUBUSER","GITHUBPASSWD","EMAIL","FULLNAME","AYSGIT","AYSBRANCH"]:
            if item not in os.environ:
                os.environ[item]=""

        C=C.format(**os.environ)

        hpath="%s/hrd/system/whoami.hrd"%basedir
        if not do.exists(path=hpath):
            do.writeFile(hpath,C)

        C="""
        #here domain=jumpscale, change name for more domains
        metadata.jumpscale =
            url:'{AYSGIT}',
            branch:'{AYSBRANCH}',

        """
        C=C.format(**os.environ)

        hpath="%s/hrd/system/atyourservice.hrd"%basedir
        if not do.exists(path=hpath):
            do.writeFile(hpath,C)

        C="""
        deactivate () {
            export PATH=$_OLD_PATH
            unset _OLD_PATH
            export PYTHONPATH=$_OLD_PYTHONPATH
            unset _OLD_PYTHONPATH
            export LD_LIBRARY_PATH=$_OLD_LD_LIBRARY_PATH
            unset _OLD_LD_LIBRARY_PATH
            export PS1=$_OLD_PS1
            unset _OLD_PS1
            unset JSBASE
            if [ -n "$BASH" -o -n "$ZSH_VERSION" ] ; then
                    hash -r 2>/dev/null
            fi
        }

        if [[ "$JSBASE" == "$base" ]]; then
            return 0
        fi

        export _OLD_PATH=$PATH
        export _OLD_PYTHONPATH=$PYTHONPATH
        export _OLD_LDLIBRARY_PATH=$LD_LIBRARY_PATH
        export _OLD_PS1=$PS1
        export PATH=$base/bin:$PATH
        export JSBASE=$base
        export PYTHONPATH=$base/lib:$base/lib/lib-dynload/:$base/bin:$base/lib/python.zip:$base/lib/plat-x86_64-linux-gnu
        #export LD_LIBRARY_PATH=$base/bin
        export PS1="(JumpScale) $PS1"
        if [ -n "$BASH" -o -n "$ZSH_VERSION" ] ; then
                hash -r 2>/dev/null
        fi
        """
        C=C.replace("$base",basedir)
        envfile = "%s/env.sh"%basedir
        do.writeFile(envfile,C)

        if not insystem:
            C2="""#!/bin/bash
            # set -x
            source {env}
            #echo sandbox:{base}
            # echo $base/bin/python "$@"
            $base/bin/python "$@"
            """
        else:
            C2="""#!/bin/bash
            # set -x
            source {env}
            #echo sandbox:{base}
            # echo $base/bin/python "$@"
            exec python "$@"
            """

        C2=C2.format(base=basedir, env=envfile)
        C2=C2.replace("$base",basedir)
        dest="%s/bin/jspython"%basedir
        do.delete(dest)
        do.writeFile(dest,C2)
        do.chmod(dest, 0o770)

        if insystem:
            #             C2="""
            # #!/bin/bash
            # set -ex
            # #export PYTHONPATH=$base/lib:$base/lib/lib-dynload/:$base/bin:$base/lib/python.zip:$base/lib/plat-x86_64-linux-gnu:$PYTHONPATH
            # /usr/bin/python "$@"
            # """
            # C2=C2.replace("$base",basedir)
            dest="/usr/local/bin/jspython"
            do.delete(dest)#to remove link

            do.writeFile(dest,C2)
            do.chmod(dest, 0o770)

            dest="/usr/bin/jspython"
            do.delete(dest)


        #change site.py file
        def changesite(path):
            if do.exists(path=path):
                C=do.readFile(path)
                out=""
                for line in C.split("\n"):
                    if line.find("ENABLE_USER_SITE")==0:
                        line="ENABLE_USER_SITE = False"
                    if line.find("USER_SITE")==0:
                        line="USER_SITE = False"
                    if line.find("USER_BASE")==0:
                        line="USER_BASE = False"

                    out+="%s\n"%line
                do.writeFile(path,out)
        changesite("%s/lib/site.py"%basedir)
        # if insystem:
        #     changesite("/usr/local/lib/python2.7/dist-packages/site.py"%basedir)




        ############# custom install items

    def cleanSystem(self):
        if self.TYPE.startswith("UBUNTU"):
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
	    rm /usr/local/bin/ays*
            rm /usr/local/bin/osis*
            rm -rf /opt/jumpscale7/lib/JumpScale
            rm -rf /opt/sentry/
            sudo stop redisac
            sudo stop redisp
            sudo stop redism
            sudo stop redisc
            killall redis-server
            rm -rf /opt/redis/
            """
            self.executeCmds(CMDS,outputStdout=False, outputStderr=False,useShell = True,log=False,cwd=None,timeout=60,errors=[],ok=[],captureout=False,dieOnNonZeroExitCode=False)

    def updateOS(self):

        if self.TYPE.startswith("UBUNTU"):
            CMDS="""
            apt-get update
            apt-get autoremove
            apt-get -f install -y
            apt-get upgrade -y
            """
            do.executeCmds(CMDS)

        elif self.TYPE.startswith("OSX"):
            CMDS="""
            brew update
            brew upgrade
            """
            do.executeCmds(CMDS)

    def installpip(self):
        if not do.exists(do.joinPaths(do.TMP,"get-pip.py")):
            cmd="cd %s;curl -k https://bootstrap.pypa.io/get-pip.py > get-pip.py;python get-pip.py"%do.TMP
            do.execute(cmd)

    def prepare(self,SANDBOX=1,base="/opt/jumpscale7",offline=False):
        # if pythonversion==2:
        #     gitbase="base_python"
        # else:
        #     gitbase="base_python3"

        if do.TYPE!=("UBUNTU64"):
            SANDBOX=0

        if SANDBOX==1:

            print ("pull binaries")
            gitbase="base_python"
            do.pullGitRepo("https://docs.greenitglobe.com/binary/%s"%gitbase,depth=1,offline=offline)

            print ("copy binaries")
            basepath = "%s/docs/binary/%s/root" % (do.CODEDIR, gitbase)
            for path in ('bin', 'lib'):
                dest = "%s/%s" % (base, path)
                src = "%s/%s"%(basepath,  path)
                do.copyTree(src, dest)
            do.copyFile("%s/ays" % basepath, "/etc/init.d/ays")

        else:
            self.installpip()
            cmds="""
            pip install ipython
            """
            do.executeCmds(cmds)

            if sys.platform.startswith('win'):
                raise RuntimeError("Cannot find JSBASE, needs to be set as env var")
            elif sys.platform.startswith('darwin'):
                cmds="""
                brew install tmux
                brew install psutil
                pip install redis
                """
                do.executeCmds(cmds)


    def prepareUbuntu14Development(self,js=True):
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

    def prepareUbuntu14(self,js=True):
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
        if name=="":
            name=email
        if email=="":
            raise RuntimeError("email cannot be empty")
        do.execute("git config --global user.email \"%s\""%email)
        do.execute("git config --global user.name \"%s\""%name)

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


do.installer=Installer()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Install JumpScale')
    parser.add_argument('-o', '--offline', required=False, default=None, help='offline mode', action='store_true')
    args = parser.parse_args()

    do.installer.installJS(offline=args.offline)
