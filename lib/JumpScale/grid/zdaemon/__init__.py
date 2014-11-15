from JumpScale import j

import JumpScale.grid.gevent
import JumpScale.baselib.key_value_store
import JumpScale.baselib.serializers

from .ZDaemonFactory import ZDaemonFactory

j.base.loader.makeAvailable(j, 'core')
j.core.zdaemon = ZDaemonFactory()

j.base.loader.makeAvailable(j, 'servers')
j.servers.zdaemon = ZDaemonFactory()
