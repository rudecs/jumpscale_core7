from JumpScale import j

def cb():
    from .Docker import Docker
    return Docker()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('docker', cb)

