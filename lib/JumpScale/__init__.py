# __version__ = '7.0.0'
# __all__ = ['__version__', 'j']


# import pkgutil
# __path__ = pkgutil.extend_path(__path__, __name__)
# del pkgutil

import sys
import os

if not 'JSBASE' in os.environ:
    if sys.version.startswith("3"):
        base="/opt/jumpscale73"
    else:    
        base="/opt/jumpscale7"
else:
    base=os.environ['JSBASE']


class Loader(object):
    def __init__(self):
        self._extensions = {}

    def _register(self, name, callback):
        self._extensions[name] = callback

    def __getattr__(self, attr):
        if attr not in self._extensions:
            raise AttributeError("%s is not loaded, did your forget an import?" % attr)
        obj = self._extensions[attr]()
        setattr(self, attr, obj)
        return obj

    def _getAttributeNames(self):
        return self._extensions.keys()

class JumpScale(Loader):
    pass

class Core(Loader):
    pass

class EventsTemp():
    def inputerror_critical(self,msg,category=""):
        print("ERROR IN BOOTSTRAP:%s"%category)
        print(msg)
        sys.exit(1)

def loadSubModules(filepath, prefix='JumpScale'):
    rootfolder = os.path.dirname(filepath)
    for module in os.listdir(rootfolder):
        moduleload = '%s.%s' % (prefix, module)
        if not os.path.isdir(os.path.join(rootfolder, module)):
            continue
        try:
            __import__(moduleload, locals(), globals())
        except ImportError, e:
            pass

j = JumpScale()

#doesn't do anything, don't see where its coming from
# from . import base

j.core=Core()
j.events=EventsTemp()

from InstallTools import *
j.do=InstallTools()

from . import core

from .core.PlatformTypes import PlatformTypes
j.system.platformtype=PlatformTypes()

from .core import pmtypes
pmtypes.register_types()
j.basetype=pmtypes.register_types()

from .core.Console import Console
j.console=Console()

from .baselib import hrd
j.application.config = j.core.hrd.get(path="%s/hrd/system"%base)

j.logger.enable=j.application.config.getBool("system.logging")

from .core.Dirs import Dirs
j.dirs=Dirs()

from .core import errorhandling

loadSubModules(__file__)

j.application.init()


