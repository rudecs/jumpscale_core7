#BOOTSTRAP CODE
#BOOTSTRAP CODE
path="/tmp/InstallTools.py"

import os
if os.environ.has_key("jsbranch"):
    branch=os.environ["jsbranch"]
else:
    branch="master"

if not os.path.exists(path):
    os.popen("curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/%s/install/InstallTools.py > /tmp/InstallTools.py"%branch)

os.chdir("/tmp")

from InstallTools import *

#look at methods in https://github.com/Jumpscale/jumpscale_core7/blob/master/install/InstallTools.py to see what can be used
#there are some easy methods to allow git manipulation, copy of files, execution of items

#there are many more functions available in jumpscale

print "install jumpscale7"
do.installJS(base="/opt/jumpscale7",clean=False)

from JumpScale import j

#j.system....
