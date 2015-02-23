from JumpScale import j

def cb():
    from .RsyncFactory import RsyncFactory
    return RsyncFactory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('rsync', cb)

