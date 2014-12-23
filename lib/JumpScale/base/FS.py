from JumpScale import j

import os
import sys

from JumpScale.baselib.installtools.InstallTools import InstallTools

class FS:

    @staticmethod           
    def log(msg):
        print(msg)

    @staticmethod       
    def fileGetContents(filename): 
        """Read a file and get contents of that file
        @param filename: string (filename to open for reading )
        @rtype: string representing the file contents
        """
        with open(filename) as fp:
            data = fp.read()
        return data    

    @staticmethod       
    def isDir( path, followSoftlink=False):
        """Check if the specified Directory path exists
        @param path: string
        @param followSoftlink: boolean
        @rtype: boolean (True if directory exists)
        """
        if FS.isLink(path) :
            if not followSoftlink:
                return False
            else:
                link=FS.readLink(path)
                return FS.isDir(link)
        else:
            return os.path.isdir(path)

    def isExecutable(path):
         stat.S_IXUSR & statobj.st_mode



    @staticmethod
    def readLink(path):
        """Works only for unix
        Return a string representing the path to which the symbolic link points.
        """
        while path[-1]=="/" or path[-1]=="\\":
            path=path[:-1]
        return os.readlink(path)

    @staticmethod       
    def isFile( path, followSoftlink = False):
        """Check if the specified file exists for the given path
        @param path: string
        @param followSoftlink: boolean
        @rtype: boolean (True if file exists for the given path)
        """
        if FS.isLink(path) :
            if not followSoftlink:
                return False
            else:
                link=FS.readLink(path)
                return FS.isFile(link)
        else:
            return os.path.isfile(path)

    @staticmethod       
    def list(path):
        # FS.log("list:%s"%path)
        if(FS.isDir(path)):
            s=["%s/%s"%(path,item) for item in os.listdir(path)]
            s.sort()
            return s
        elif(FS.isLink(path)):
            link=FS.readLink(path)
            return FS.list(link)
        else:
            raise ValueError("Specified path: %s is not a Directory in FS.listDir"% path)

    installtools=InstallTools()

    @staticmethod
    def exists(path):
        return os.path.exists(path)

    @staticmethod
    def findDependencies(path,deps={}):
        excl=["libc.so","libpthread.so","libutil.so"]
        out=FS.installtools.execute("ldd %s"%path)
        result=[]
        for item in [item.strip() for item in out.split("\n") if item.strip()!=""]:
            if item.find("=>")!=-1:
                link=item.split("=>")[1].strip()
                link=link.split("(")[0].strip()
                if FS.exists(link):
                    name=os.path.basename(link)
                    if not deps.has_key(name):
                        print(link)
                        deps[name]=link
                        deps=FS.findDependencies(link)
        return deps

    @staticmethod
    def copyDependencies(path,dest):
        FS.installtools.createdir(dest)
        deps=FS.findDependencies(path)
        for name in deps.keys():
            path=deps[name]
            FS.installtools.copydeletefirst(path,"%s/%s"%(dest,name))
        

j.base.fs=FS

