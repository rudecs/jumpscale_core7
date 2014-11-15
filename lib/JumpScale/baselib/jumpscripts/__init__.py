from JumpScale import j

from .JumpscriptFactory import JumpscriptFactory

j.base.loader.makeAvailable(j, 'tools')
j.core.jumpscripts = JumpscriptFactory()
