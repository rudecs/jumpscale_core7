from JumpScale import j

from .RsyncFactory import RsyncFactory

j.base.loader.makeAvailable(j, 'tools')
j.tools.rsync = RsyncFactory()

