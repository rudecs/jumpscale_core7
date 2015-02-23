from JumpScale import j

def cb():
    from .StatManager import StatManager
    return StatManager()

j.base.loader.makeAvailable(j, 'system')
j.system._register('statmanager', cb)
