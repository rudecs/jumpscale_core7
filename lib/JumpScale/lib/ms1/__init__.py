from JumpScale import j

def cb():
    from .ms1 import MS1Factory
    return MS1Factory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('ms1', cb)
