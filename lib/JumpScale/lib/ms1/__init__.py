from JumpScale import j

def cb():
    from .ms1 import MS1
    return MS1()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('ms1', cb)
