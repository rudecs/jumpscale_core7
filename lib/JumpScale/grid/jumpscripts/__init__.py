from JumpScale import j

from .JumpscriptFactory import JumpscriptFactory

j.base.loader.makeAvailable(j, 'core')
j.core.jumpscripts = JumpscriptFactory()
