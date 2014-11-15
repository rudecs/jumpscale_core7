import os

from JumpScale import j

class OsisPyApps:

    def __init__(self, appName):
        self.appName = appName
        self.components = [('passwd', ''), ('login', self.appName),
                        ('database', self.appName),('ip', '127.0.0.1')]

    def generate_cfg(self):
        iniFile = j.system.fs.joinPaths(j.dirs.cfgDir, 'osisdb.cfg')
        if os.path.isfile(iniFile):
            ini = j.tools.inifile.open(iniFile)
        else:
            ini = j.tools.inifile.new(iniFile)

        exists = ini.checkSection(self.appName)
        if not exists:
            ini.addSection(self.appName)
            for key, value in self.components:
                ini.addParam(self.appName, key, value)
        ini.write()
