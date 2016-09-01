from JumpScale import j


def cb():
    from .qos import QOS
    return QOS()

j.system._register('qos', cb)
