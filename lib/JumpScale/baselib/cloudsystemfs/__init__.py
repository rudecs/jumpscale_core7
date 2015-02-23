from JumpScale import j

def cb():
    from .CloudSystemFS import CloudSystemFS
    return CloudSystemFS()

j.base.loader.makeAvailable(j, 'cloud.system')
j.cloud.system._register('fs', cb)

