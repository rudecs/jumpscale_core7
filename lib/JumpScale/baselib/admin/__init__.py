from JumpScale import j

from .Admin import *

j.base.loader.makeAvailable(j, 'tools')

j.tools.admin=AdminFactory()
