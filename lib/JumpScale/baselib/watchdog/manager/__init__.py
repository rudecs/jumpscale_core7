from JumpScale import j

from .WatchdogFactory import *

j.base.loader.makeAvailable(j, 'tools.watchdog')

j.tools.watchdog.manager=WatchdogFactory()
