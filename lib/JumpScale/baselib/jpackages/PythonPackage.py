from JumpScale import j
import re

class PythonPackage(object):
    def __init__(self):
        self._checked=False
        self._usrPathCache=[]
        self._pythonPathCache=[]
        # j.logger.addConsoleLogCategory("python")

    def clearcache(self):
        j.logger.log("Clear pathscache for /usr & python packages.",level=5,category="python.package")
        self.__init__()

    def _getPythonPathNames(self):
        if self._pythonPathCache==[]:
            j.logger.log("getpython path names and cache.",level=5,category="python.package")
            for path in j.application.config.getListFromPrefix("python.paths"):
                if not path:
                    continue
                for item in j.system.fs.listFilesAndDirsInDir(path,recursive=True):
                    item=item.lower()
                    self._pythonPathCache.append(item)   
            self._pythonPathCache.sort()  
        return  self._pythonPathCache

    def _getUsrPathNames(self):
        
        if self._usrPathCache==[]:
            j.logger.log("get /usr path names and cache.",level=5,category="python.package")
            
            for path in j.application.config.getListFromPrefix("python.paths"):
                if path.strip()=="":
                    continue
                for item in j.system.fs.listFilesAndDirsInDir(path,recursive=True):
                    item=item.lower()
                    self._usrPathCache.append(item)   
            self._usrPathCache.sort()  
        return  self._usrPathCache

    def check(self):
        return
        
    def install(self, name, version=None, latest=True):
        self.check()
        if version:
            j.system.process.execute("pip install '%s%s'" % (name, version))
        elif latest:
            j.system.process.execute("pip install '%s' --upgrade" % name)
        else:
            j.system.process.execute("pip install '%s'" % name)

    def remove(self,names,clearcache=True):
        """
        @param names can be 1 name as str or array when list
        will look in all possible python paths & remove the python lib
        """
        if j.basetype.list.check(names):
            for name in names:
                self.remove(name,clearcache=False)
            self.clearcache()
        else:
            self.check()
            name2=names.lower().strip()
            # name2=name2.replace("python","")
            res=j.system.platform.ubuntu.findPackagesInstalled(name2)
            ok=False
            for item in res:
                item2=item.lower().strip()
                if item2.find("python") != -1 or item2.find("py")==0:
                    #found python package installed through aptget, remove
                    j.system.platform.ubuntu.remove(item)

            for item, version in j.system.platform.python.list():
                if item.lower() == name2:
                    j.system.process.execute("pip uninstall -y %s" % item)

            
            #get paths from python out of config
            # print "FIND TO REMOVE:%s"%name2
            for path in self._getUsrPathNames():
                if path.find(name2) != -1:
                    if path.find("ipython")==-1:                        
                        try:
                            j.system.fs.remove(path, onlyIfExists=True)
                            # print "removed:%s"%path
                        except:
                            pass

                # print "remove %s from python dir:%s"%(name,path)
            if clearcache:
                self.clearcache()

    def list(self):
        exitcode, output = j.system.process.execute("pip list",dieOnNonZeroExitCode=False)
        if exitcode>0:
            # print "WARNING CMD 'PIP LIST' IS GIVING ERRORS, PLEASE CHECK, IMPORTANT"   
            pass     
        rec = re.compile("^(?P<name>[\w-]+)\s+\((?P<version>[\w\.]+)\)", re.M)
        return rec.findall(output)
        #@todo fix P1


    def getSitePackagePathLocal(self):
        self.check()
        if j.application.sandbox:
            base=j.system.fs.joinPaths(j.dirs.baseDir,"libext")
        else:
            base=j.application.config.get("python.paths.local.sitepackages")

        return base

    def copyLibsToLocalSitePackagesDir(self,rootpath,remove=True):
        """
        list all files and dirs in specified path and for each one call
        self.copyLibToLocalSitePackagesDir
        """
        self.check()
        for item in j.system.fs.listFilesAndDirsInDir(rootpath):
            self.copyLibToLocalSitePackagesDir(item,remove=remove)

    def copyLibToLocalSitePackagesDir(self,path,remove=True):
        """
        copy library to python.paths.local.sitepackages config param in main jumpscale hrd 
        eg. for ubuntu is: /usr/local/lib/python2.7/site-packages/
        does this for 1 lib, so the dir needs to be the library by itself
        """
        self.check()
        
        sitepackagepath=self.getSitePackagePathLocal()
        base=j.system.fs.getBaseName(path)
        dest=j.system.fs.joinPaths(sitepackagepath,base)
        if remove:
            self.remove(base)
        j.logger.log("copy python lib from %s to %s"%(path,dest),5,category="python.install")
        if j.system.fs.isFile(path):
            j.system.fs.copyFile(path, dest, createDirIfNeeded=True, skipProtectedDirs=False, overwriteFile=True)
        else:
            j.system.fs.copyDirTree(path,dest, keepsymlinks=False, eraseDestination=remove, skipProtectedDirs=False, overwriteFiles=True)

