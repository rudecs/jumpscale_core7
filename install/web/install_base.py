
#BOOTSTRAP CODE
from urllib import urlopen
import random
handle = urlopen("https://raw.githubusercontent.com/Jumpscale/jumpscale_core/master/install/InstallTools.py?%s"%random.randint(1, 10000000))
exec(handle.read())

print do.prepareUbuntu14Development(js=True)
