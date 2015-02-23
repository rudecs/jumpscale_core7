from JumpScale import j

def cb():
    from .BackupFactory import *
    import JumpScale.baselib.hash
    return BackupFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('backup', cb)
