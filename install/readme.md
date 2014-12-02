Install of jumpscale 
=====================

use these install scripts to make your life easy

```
#if ubuntu is in recent state & apt get update was done recently
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install_python.sh | bash
#or (note gevent & fabric not working on python 3.4)
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install_python34.sh | bash
```

to use
------
allways make sure you have set your env variables by
```
source /opt/jumpscale73/env.sh
```

to get shell
```
source /opt/jumpscale73/env.sh;python3 -c "from IPython import embed;embed()"
```

example through ipython
```
source /opt/jumpscale73/env.sh
ipython3
from JumpScale import j
```
use ipython or ipython3 depending python 2 or 3
same for python

more examples for installing 
----------------------------

```
#if ubuntu is in recent state & apt get update was done recently
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh | bash

#or to also update/upgrade ubuntu first
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install_updateubuntu.sh | bash

#now just install in system, not sandboxed
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install_in_system.sh | bash
```

this will do all required to install jumpscale 7 on ubuntu 14.04 in /opt/jumpscale7

all will be in sandbox, system will not be changed
