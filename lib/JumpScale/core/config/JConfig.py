
from JumpScale import j
from JumpScale.baselib.inifile.IniFile import IniFile

class JConfig():
    """
    jumpscale singleton class available under j.config
    Meant for non interactive access to configuration items
    """
    def getInifile(self, configtype, directory='jsconfig'):
        fileAlreadyExists = j.system.fs.exists(self._buildPath(configtype, directory))
        return IniFile(self._buildPath(configtype, directory), create=(not fileAlreadyExists))
    
    def getConfig(self, configtype, directory='jsconfig'):
        """
        Return dict of dicts for this configuration.
        E.g. { 'jumpscale.org'    : {url:'http://jumpscale.org', login='test'} ,
               'trac.qlayer.com' : {url:'http://trac.qlayer.com', login='mylogin'} }
        """
        ini = self.getInifile(configtype, directory)
        return ini.getFileAsDict()
    
    def remove(self, configtype, directory='jsconfig'):
        j.system.fs.remove(self._buildPath(configtype))
        
    def list(self):
        """
        List all configuration types available.
        """
        jsconfigPath = j.dirs.cfgDir
        fullpaths = []
        if j.system.fs.exists(jsconfigPath):
            fullpaths.extend(j.system.fs.listFilesInDir(jsconfigPath, filter='*.cfg'))
        return [j.system.fs.getBaseName(jsconfigPath)[:-4] for jsconfigPath in fullpaths]

    def _buildPath(self, configtype, directory='jsconfig'):
        return j.system.fs.joinPaths(j.dirs.cfgDir, directory, configtype + ".cfg")cfgDir