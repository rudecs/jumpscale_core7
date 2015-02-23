from JumpScale import j

def cb():
    from .StartupManager import StartupManager
    return StartupManager()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('startupmanager', cb)
