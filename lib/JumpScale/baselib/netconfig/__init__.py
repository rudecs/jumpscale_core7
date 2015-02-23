from JumpScale import j

def cb():
    from .Netconfig import Netconfig
    return Netconfig()

j.system._register('netconfig', cb)


