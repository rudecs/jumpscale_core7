#BOOTSTRAP CODE
from InstallTools import *

#look at methods in https://github.com/Jumpscale/jumpscale_core7/blob/master/install/InstallTools.py to see what can be used
#there are some easy methods to allow git manipulation, copy of files, execution of items 

#there are many more functions available in jumpscale

do.installJS(base="/opt/jumpscale7",clean=False,pythonversion=3,web=True)

from JumpScale import j

#j.system....