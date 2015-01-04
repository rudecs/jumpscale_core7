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


class JumpScale():
	def __init__(self):
		pass

class Core():
    def __init__(self):
        pass


# class Tools():
#     def __init__(self):
#         pass

# class Logger():
#     def __init__(self):
#         inlog=False        
#     def log(self,msg,**args):
#         print msg
# j.logger=Logger

class EventsTemp():
    def inputerror_critical(self,msg,category=""):
        print("ERROR IN BOOTSTRAP:%s"%category)
        print(msg)
        sys.exit(1)

j = JumpScale()
from . import base

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

from .core.Dirs import Dirs
j.dirs=Dirs()

# from JumpScale.core.baseclasses.BaseEnumeration import enumerations
# j.enumerators=enumerations

from .core import errorhandling

# import JumpScale.baselib.codeexecutor
from .baselib import tags
from .baselib import platforms
# from .core import config
from .baselib import hrd

from .baselib import jpackages

# import JumpScale.baselib.startupmanager
# from . import shellconfig
# from . import gui


j.application.init()


