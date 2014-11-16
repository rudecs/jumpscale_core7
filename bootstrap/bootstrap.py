#BOOTSTRAP CODE
from urllib import urlopen
import random
handle = urlopen("https://raw.githubusercontent.com/Jumpscale/jumpscale_core/master/install/InstallTools.py?%s"%random.randint(1, 10000000)) #this is to protect against caching proxy servers
exec(handle.read())


#look at methods in https://github.com/Jumpscale/jumpscale_core7/blob/master/install/InstallTools.py to see what can be used
#there are some easy methods to allow git manipulation, copy of files, execution of items 

#there are many more functions available in jumpscale

from JumpScale import j

from IPython import embed
print "DEBUG NOW ll"
embed()


do.installJS(base="/opt/jumpscale7",clean=True)

from JumpScale import j

#j.system....