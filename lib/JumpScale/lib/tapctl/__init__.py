from JumpScale import j


def cb():
    from .tapctl import TAPCTL
    return TAPCTL()


j.tools._register('tapctl', cb)
