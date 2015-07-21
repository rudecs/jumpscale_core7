#BOOTSTRAP CODE


import os

if os.environ.has_key("JSBRANCH"):
    branch=os.environ["JSBRANCH"]
else:
    branch="master"

if os.environ.has_key("TMPDIR"):
    tmpdir=os.environ["TMPDIR"]
else:
    tmpdir="/tmp"

os.chdir(tmpdir)

print "bootstrap installtools in dir %s and use branch:'%s'"%(tmpdir,branch)

#GET THE MAIN INSTALL TOOLS SCRIPT

path="%s/InstallTools.py"%tmpdir

overwrite=True #set on False for development or debugging

if overwrite and os.path.exists(path):
    os.remove(path)
    os.remove(path+"c")

if not os.path.exists(path):
    print "overwrite"
    os.popen("curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/%s/install/InstallTools.py > %s"%(branch,path))

from InstallTools import *


#look at methods in https://github.com/Jumpscale/jumpscale_core7/blob/master/install/InstallTools.py to see what can be used
#there are some easy methods to allow git manipulation, copy of files, execution of items

#there are many more functions available in jumpscale

#FROM now on there is a do. variable which has many features, please investigate


print "install jumpscale7"
do.installer.installJS()

from JumpScale import j

#j.system....
