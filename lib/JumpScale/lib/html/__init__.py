from JumpScale import j

def cb():
    from .HTMLFactory import HTMLFactory
    return HTMLFactory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('html', cb)

