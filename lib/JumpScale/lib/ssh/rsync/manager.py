import os
import re

from StringIO import StringIO
from fabric.api import settings


CONFIG_FILE = '/etc/rsyncd.conf'

# EXPORT_OPT_REGEXT = re.compile('^(?:([\w/]+)|"([\w\s/]+)")\s+(.+)$')
# CLIENT_OPT_REGEXT = re.compile('\s*([^\(]+)\(([^\)]+)\)')


class RsyncError(Exception):
    pass

class RsyncModule(object):
    def __init__(self, name=None):
        self.name = name
        self.params = {}

    def set(self, key, value):
        self.params[key] = value

    def get(self, key, value):
        if key not in self.params:
            raise RsyncError('not parameter %s in modules %s' % (key, self.name))

        return self.params[key]

    def __str__(self):
        buf = StringIO()
        buf.write('[%s]\n' % self.name)
        for k, v in self.params.iteritems():
            buf.write('\t%s = %s\n' % (k, v))

        return buf.getvalue()

    def __repr__(self):
        return str(self)

class Rsync(object):
    def __init__(self, con=None):
        self._con = con
        self._modules = None
        self._globalParams = {}

    def _load(self):
        modules = {}
        globalParams = {}
        currentModule = None

        with settings(abort_exception=RsyncError):
            content = self._con.file_read(CONFIG_FILE)
            lineparts = []
            for linepart in content.split(os.linesep):
                linepart = linepart.strip()
                if linepart == '' or linepart.startswith('#'):
                    continue

                lineparts.append(linepart)

                if linepart.endswith('\\'):
                    lineparts.append(linepart)
                    continue

                line = ' '.join(lineparts)
                lineparts = []

                if line.startswith('['):
                    # begining of a module
                    end = line.find(']')
                    name = line[1:end]
                    modules[name] = RsyncModule(name)
                    currentModule = name
                    continue
                elif line.find('=') != -1:
                    i = line.find('=')
                    key = line[:i].strip()
                    value = line[i+1:].strip()
                    if currentModule is None:
                        # global param
                        globalParams[key] = value
                    else:
                        # module param
                        modules[currentModule].set(key, value)
                    continue
        self._modules = modules
        self._globalParams = globalParams

    def start(self):
        """start rsync daemon"""
        self._con.sudo('rsync --daemon --config=%s' % CONFIG_FILE)

    def stop(self):
        """stop rsync daemon"""
        self._con.sudo('pkill rsync')

    def restart(self):
        """restart rsync daemon"""
        self.stop()
        self.start()

    @property
    def params(self):
        """return the global parameters"""
        if self._modules is None:
            self._load()

        return self._globalParams

    def setParams(self, key, value):
        """set a global parameter"""
        self._globalParams[key] = value

    def removeParams(self, key):
        """remove a global parameter"""
        if self._modules is None:
            self._load()

        if key in self._globalParams:
            self._globalParams.pop(key)

    def addModule(self, name):
        """add a module
           mod = rsync.addModule('share')
           mod.set('path', '/tmp/share')
           rs.commit()
        """
        if self._modules is None:
            self._load()

        self._modules[name] = RsyncModule(name)
        return self._modules[name]

    def removeModule(self, name):
        if self._modules is None:
            self._load()

        if name in self._modules:
            self._modules.pop(name)

    def commit(self):
        buf = StringIO()

        with settings(abort_exception=RsyncError):
            buf.write(str(self))
            self._con.file_write(CONFIG_FILE, buf.getvalue(), mode=644)
        self.restart()

    def erase(self):
        self._globalParams = {}
        self._modules = {}

    @property
    def modules(self):
        if self._modules is None:
            self._load()
        return self._modules.values()

    def __str__(self):
        if self._modules is None:
            self._load()

        buf = StringIO()
        for k, v in self._globalParams.iteritems():
            buf.write('%s = %s\n' % (k, v))

        buf.write('\n')

        for m in self._modules.values():
            buf.write(str(m))
            buf.write('\n')

        return buf.getvalue()

    def __repr__(self):
        return str(self)

class RsyncFactory(object):
    def _getFactoryEnabledClasses(self):
        return (("","RsyncModule",RsyncModule()),("","Rsync",Rsync()))    
    def get(self, con):
        return Rsync(con)
