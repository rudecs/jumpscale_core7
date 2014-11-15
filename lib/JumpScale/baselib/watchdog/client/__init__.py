from JumpScale import j

from .WatchdogClient import *

j.base.loader.makeAvailable(j, 'tools.watchdog')

j.tools.watchdog.client=WatchdogClient()
