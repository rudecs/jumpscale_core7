from JumpScale import j

def cb():
    from .NetConfigFactory import NetConfigFactory
    return NetConfigFactory()

j.system._register('ovsnetconfig', cb)

