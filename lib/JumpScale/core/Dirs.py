
import sys, os, inspect
import tempfile

from JumpScale import j

def pathToUnicode(path):
    """
    Convert path to unicode. Use the local filesystem encoding. Will return
    path unmodified if path already is unicode.

    @param path: path to convert to unicode
    @type path: basestring
    @return: unicode path
    @rtype: unicode
    """
    if isinstance(path, str):
        return path

    return path.decode(sys.getfilesystemencoding())

class Dirs(object):
    """Utility class to configure and store all relevant directory paths"""


    def __init__(self):
        '''jumpscale sandbox base folder'''
        self.__initialized = False ##bool

        import sys

        self._hrdDir=None
        self._serviceTemplateDir=None
       
        self.baseDir=j.application.config.get("system.paths.base")
        self.appDir = j.application.config.get("system.paths.app")
        self.varDir = j.application.config.get("system.paths.var")
        self.cfgDir = j.application.config.get("system.paths.cfg")
        self.libDir = j.application.config.get("system.paths.lib")
        self.jsLibDir = j.application.config.get("system.paths.python.lib.js")
        self.logDir = j.application.config.get("system.paths.log")
        self.pidDir = j.application.config.get("system.paths.pid")
        self.codeDir = j.application.config.get("system.paths.code")
        self.libExtDir = j.application.config.get("system.paths.python.lib.ext")

        self.tmpDir = tempfile.gettempdir()

        self.gitConfigDir="unknown"

        self._createDir(os.path.join(self.baseDir,"libext"))

        if self.libDir in sys.path:
            sys.path.pop(sys.path.index(self.libDir))
        sys.path.insert(0,self.libDir)

        pythonzip = os.path.join(self.libDir, 'python.zip')
        if os.path.exists(pythonzip):
            if pythonzip in sys.path:
                sys.path.pop(sys.path.index(pythonzip))
            sys.path.insert(0,pythonzip)

        if self.libExtDir in sys.path:
            sys.path.pop(sys.path.index(self.libExtDir))
        sys.path.insert(2,self.libExtDir)

        # self.packageDir = os.path.join(self.varDir,"jpackages")
        # self._createDir(self.packageDir)

        if 'JSBASE' in os.environ:
            self.binDir = os.path.join(self.baseDir, 'bin')
        else:
            self.binDir = j.application.config.get("system.paths.bin")

    def replaceTxtDirVars(self,txt,additionalArgs={}):
        """
        replace $base,$vardir,$cfgDir,$bindir,$codedir,$tmpdir,$logdir,$appdir with props of this class
        """
        txt=txt.replace("$base",self.baseDir)
        txt=txt.replace("$appdir",self.appDir)
        txt=txt.replace("$codedir",self.codeDir)
        txt=txt.replace("$vardir",self.varDir)
        txt=txt.replace("$cfgDir",self.cfgDir)
        txt=txt.replace("$hrdDir",self._hrdDir)
        txt=txt.replace("$bindir",self.binDir)
        txt=txt.replace("$logdir",self.logDir)
        txt=txt.replace("$tmpdir",self.tmpDir)
        txt=txt.replace("$libdir",self.libDir)
        txt=txt.replace("$jslibextdir",self.libExtDir)
        txt=txt.replace("$jsbindir",self.binDir)
        txt=txt.replace("$nodeid",str(j.application.whoAmI.nid))
        txt=txt.replace("$jumpscriptsdir", j.core.jumpscripts.basedir)
        for key,value in additionalArgs.items():
            txt=txt.replace("$%s"%key,str(value))
        return txt

    # def replaceFilesDirVars(self,path,recursive=True, filter=None,additionalArgs={}):
    #     if j.system.fs.isFile(path):
    #         paths=[path]
    #     else:
    #         paths=j.system.fs.listFilesInDir(path,recursive,filter)

    #     for path in paths:
    #         content=j.system.fs.fileGetContents(path)
    #         content2=self.replaceTxtDirVars(content,additionalArgs)
    #         if content2!=content:
    #             j.system.fs.writeFile(filename=path,contents=content2)

    def _createDir(self,path):
        if not os.path.exists(path):
            os.makedirs(path)

    @property
    def hrdDir(self):
        if self.amInGitConfigRepo()!=None:
            self._hrdDir="%s/services/"%(self.amInGitConfigRepo())
        else:
            # path = j.system.fs.joinPaths(j.application.config.get("system.paths.hrd"),"apps")
            self._hrdDir = j.application.config.get("system.paths.hrd")
        return self._hrdDir

    def getHrdDir(self,system=False):
        hrdDir = ""
        if system==False :
            hrdDir = self.amInGitConfigRepo()
            if hrdDir != None:
                hrdDir = self.hrdDir
            else:
                hrdDir = self.hrdDir+"/apps"
        else:
            hrdDir = self.hrdDir+"/system"
        if not j.system.fs.exists(hrdDir):
            j.system.fs.createDir(hrdDir)
        return  hrdDir

    @property
    def serviceTemplateDir(self):
        if self._serviceTemplateDir!=None:
            return self._serviceTemplateDir
        if self.amInGitConfigRepo()!=None:
            self._serviceTemplateDir=j.system.fs.joinPaths(self.amInGitConfigRepo(),"servicetemplates")
        else:
            raise RuntimeError("should be in a git config repo")
        return self._serviceTemplateDir


    def init(self,reinit=False):
        """Initializes all the configured directories if needed

        If a folder attribute is None, set its value to the corresponding
        default path.

        @returns: Initialization success
        @rtype: bool
        """

        if reinit==False and self.__initialized == True:
            return True

        # if j.system.platformtype.isWindows() :
        #     self.codeDir=os.path.join(self.baseDir, 'code')

        # self.loadProtectedDirs()

        self.__initialized = True
        return True

    def _getParent(self, path):
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

    def _getLibPath(self):
        parent = self._getParent
        libDir=parent(parent(__file__))
        libDir=os.path.abspath(libDir).rstrip("/")
        return libDir

    def getPathOfRunningFunction(self,function):
        return inspect.getfile(function)

    def loadProtectedDirs(self):
        return
        protectedDirsDir = os.path.join(self.cfgDir, 'debug', 'protecteddirs')
        if not os.path.exists(protectedDirsDir):
            self._createDir(protectedDirsDir)
        _listOfCfgFiles = j.system.fs.listFilesInDir(protectedDirsDir, filter='*.cfg')
        _protectedDirsList = []
        for _cfgFile in _listOfCfgFiles:
            _cfg = open(_cfgFile, 'r')
            _dirs = _cfg.readlines()
            for _dir in _dirs:
                _dir = _dir.replace('\n', '').strip()
                if j.system.fs.isDir(_dir):
                    # npath=j.system.fs.pathNormalize(_dir)
                    if _dir not in _protectedDirsList:
                        _protectedDirsList.append(_dir)
        self.protectedDirs = _protectedDirsList


    def addProtectedDir(self,path,name="main"):
        if j.system.fs.isDir(path):
            path=j.system.fs.pathNormalize(path)
            configfile=os.path.join(self.cfgDir, 'debug', 'protecteddirs',"%s.cfg"%name)
            if not j.system.fs.exists(configfile):
                j.system.fs.writeFile(configfile,"")
            content=j.system.fs.fileGetContents(configfile)
            if path not in content.split("\n"):
                content+="%s\n"%path
                j.system.fs.writeFile(configfile,content)
            self.loadProtectedDirs()

    def removeProtectedDir(self,path):
        path=j.system.fs.pathNormalize(path)
        protectedDirsDir = os.path.join(self.cfgDir, 'debug', 'protecteddirs')
        _listOfCfgFiles = j.system.fs.listFilesInDir(protectedDirsDir, filter='*.cfg')
        for _cfgFile in _listOfCfgFiles:
            _cfg = open(_cfgFile, 'r')
            _dirs = _cfg.readlines()
            out=""
            found=False
            for _dir in _dirs:
                _dir = _dir.replace('\n', '').strip()
                if _dir==path:
                    #found, need to remove
                    found=True
                else:
                    out+="%s\n"%_dir
            if found:
                j.system.fs.writeFile(_cfgFile,out)
                self.loadProtectedDirs()


    def checkInProtectedDir(self,path):
        return
        #@todo reimplement if still required
        path=j.system.fs.pathNormalize(path)
        for item in self.protectedDirs :
            if path.find(item)!=-1:
                return True
        return False

    def _gitConfigRepo(self,path):
        if self.gitConfigDir!=None and self.gitConfigDir!="unknown":
            return self.gitConfigDir
        while path.strip("/")!="":
            if ".git" in j.system.fs.listDirsInDir(path, recursive=False, dirNameOnly=True, findDirectorySymlinks=False) and\
            "servicetemplates"  in j.system.fs.listDirsInDir(path, recursive=False, dirNameOnly=True, findDirectorySymlinks=False):
                self.gitConfigDir=path
                return path
            path=j.system.fs.getParent(path)
        self.gitConfigDir=None
        return None

    def isGitConfigRepo(self,path):
        if self._gitConfigRepo(path) != None:
            return True
        return False

    def amInGitConfigRepo(self):
        """
        return parent path where .git is or None when not found
        """
        path=j.system.fs.getcwd()
        return self._gitConfigRepo(path)

    def createGitConfigRepo(self,path):
        j.system.fs.createDir(j.system.fs.joinPaths(path,"services"))
        j.system.fs.createDir(j.system.fs.joinPaths(path,"servicetemplates"))
        j.system.fs.createDir(j.system.fs.joinPaths(path,".git"))

    def __str__(self):
        return str(self.__dict__) #@todo P3 implement (thisnis not working)

    __repr__=__str__
