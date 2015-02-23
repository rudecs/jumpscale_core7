from JumpScale import j

def cbb():
    from .units import Bytes
    return Bytes()

def cbs():
    from .units import Sizes
    return Sizes()

j.base.loader.makeAvailable(j, 'tools.units')
j.tools.units._register('bytes', cbb)
j.tools.units._register('sizes', cbs)
