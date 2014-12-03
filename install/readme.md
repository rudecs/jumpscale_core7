Install of jumpscale 
=====================

use these install scripts to make your life easy

```
#if ubuntu is in recent state & apt get update was done recently
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install_python.sh | bash

#if you also want to have the web packages 
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install_python_web.sh | bash

#or (note gevent & fabric not working on python 3.4)
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install_python34.sh | bash
```

to use in sandbox
-----------------
allways make sure you have set your env variables by
```
source /opt/jumpscale7/env.sh
```

to get shell
```
source /opt/jumpscale7/env.sh;python3 -c "from IPython import embed;embed()"
```

example through ipython
```
source /opt/jumpscale7/env.sh
ipython
from JumpScale import j
```
use ipython or ipython3 depending python 2 or 3
same for python
