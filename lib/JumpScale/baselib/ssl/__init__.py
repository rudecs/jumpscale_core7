from JumpScale import j
from .SSL import SSL
j.base.loader.makeAvailable(j, 'tools')
j.tools.ssl = SSL()
