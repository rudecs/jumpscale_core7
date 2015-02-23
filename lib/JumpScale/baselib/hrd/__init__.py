from JumpScale import j

def cb():
    from .HRDFactory import HRDFactory
    return HRDFactory()

j.core._register('hrd', cb)
