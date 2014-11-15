# __version__ = '6.0.0'
# __all__ = ['__version__', 'j']


# import pkgutil
# __path__ = pkgutil.extend_path(__path__, __name__)
# del pkgutil

import sys
import os

if not 'JSBASE' in os.environ:
    base="/opt/jumpscale7"
else:
    base=os.environ['JSBASE']
#     home = os.environ['JSBASE']
#     sys.path=['', '%s/bin'%home,'%s/bin/core.zip'%home,'%s/lib'%home,'%s/libjs'%home,\
#         '%s/lib/python.zip'%home,'%s/libext'%home,'%s/lib/JumpScale.zip'%home]

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
    def inputerror_critical(self,msg,category):
        print "ERROR IN BOOTSTRAP"
        print msg
        sys.exit(1)

j = JumpScale()

j.core=Core()
j.events=EventsTemp()

from InstallTools import *
j.do=InstallTools()

from . import core

from core.PlatformTypes import PlatformTypes
j.system.platformtype=PlatformTypes()

from core import pmtypes
pmtypes.register_types()
j.basetype=pmtypes.register_types()

from core.Console import Console
j.console=Console()

import baselib.hrd
j.application.config = j.core.hrd.getHRD(path="%s/hrd"%base)

from core.Dirs import Dirs
j.dirs=Dirs()

# from JumpScale.core.baseclasses.BaseEnumeration import enumerations
# j.enumerators=enumerations

from core import errorhandling

# import JumpScale.baselib.codeexecutor
import baselib.tags
import baselib.platforms
import core.config
import baselib.hrd

# import JumpScale.baselib.startupmanager
# from . import shellconfig
# from . import gui

j.application.init()


