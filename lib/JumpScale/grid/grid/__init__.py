from JumpScale import j
from .GridFactory import GridFactory
j.base.loader.makeAvailable(j, 'core')
j.core.grid = GridFactory()
