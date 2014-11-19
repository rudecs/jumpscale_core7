Install of jumpscale 
=====================

use these install scripts to make your life easy

```
#if ubuntu is in recent state & apt get update was done recently
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install_python34.sh | bash
```

more examples

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
