JumpScale 7
===========

[![Build Status](http://ci.codescalers.com/buildStatus/icon?job=Jumpscale7-build)](http://ci.codescalers.com/job/Jumpscale7-build/)

JumpScale is A cloud automation product and a branch from what used to be Pylabs. About 7 years ago Pylabs was the basis of a cloud automation product which was acquired by SUN Microsystems from a company called Q-Layer. In the mean time we are 4 versions further and we rebranded to JumpScale. The latest release is [Jumpscale 8](https://github.com/jumpscale/jumpscale_core8).

documentation see 
https://gig.gitbooks.io/jumpscale/content/

##Install jumpscale

```bash
sudo -s
#if ubuntu is in recent state & apt get update was done recently
export AYSBRANCH=master
export JSBRANCH=master
cd /tmp;rm -f install.sh;curl -k https://raw.githubusercontent.com/jumpscale7/jumpscale_core7/master/install/install.sh > install.sh;bash install.sh
```

api doc (generated out of code)
- https://gig.gitbooks.io/jumpscaleapi/content/
