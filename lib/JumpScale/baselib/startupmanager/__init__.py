from JumpScale import j
from .StartupManager import StartupManager

j.base.loader.makeAvailable(j, 'tools')
j.tools.startupmanager = StartupManager()
