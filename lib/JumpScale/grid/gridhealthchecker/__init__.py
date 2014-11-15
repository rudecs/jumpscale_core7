from JumpScale import j
from .gridhealthchecker import GridHealthChecker
j.base.loader.makeAvailable(j.core, 'grid')
j.core.grid.healthchecker = GridHealthChecker()
