from JumpScale import j
from .StatManager import StatManager

j.base.loader.makeAvailable(j, 'system')
j.system.statmanager = StatManager()
