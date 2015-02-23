from JumpScale import j

def cb():
    from .GridFactory import GridFactory
    return GridFactory()

j.base.loader.makeAvailable(j, 'core')
j.core._register('grid', cb)
