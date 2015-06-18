Install of jumpscale 
=====================

use these install scripts to make your life easy

```
#if ubuntu is in recent state & apt get update was done recently
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh

```

to use in sandbox
-----------------
allways make sure you have set your env variables by
```
source /opt/jumpscale7/env.sh
```

to get shell
```
source /opt/jumpscale7/env.sh;python -c "from IPython import embed;embed()"
```

example through ipython
```
source /opt/jumpscale7/env.sh
ipython
from JumpScale import j
```

