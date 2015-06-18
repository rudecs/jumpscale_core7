#BOOTSTRAP CODE

path="/tmp/InstallTools.py"

import os
if not os.path.exists(path):	
	os.popen("curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/InstallTools.py > /tmp/InstallTools.py")

from InstallTools import *

#	try:
#    	from urllib3.request import urlopen
#	except ImportError:
#    	from urllib import urlopen
#	import random
#	handle = urlopen("https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/InstallTools.py?%s"%random.randint(1, 10000000)) #this is to protect against caching proxy servers
#	code=handle.read()
	

#look at methods in https://github.com/Jumpscale/jumpscale_core7/blob/master/install/InstallTools.py to see what can be used
#there are some easy methods to allow git manipulation, copy of files, execution of items

#there are many more functions available in jumpscale

print "install jumpscale7"
do.installJS(base="/opt/jumpscale7",clean=True,insystem=True,pythonversion=2,web=True)

from JumpScale import j

#j.system....
