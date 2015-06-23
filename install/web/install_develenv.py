
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

print do.prepareUbuntu14Development(js=True)

from JumpScale import j
