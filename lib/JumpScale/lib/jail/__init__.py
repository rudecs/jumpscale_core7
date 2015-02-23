from JumpScale import j

def cb():
    from .JailFactory import JailFactory
    return JailFactory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('jail', cb)
