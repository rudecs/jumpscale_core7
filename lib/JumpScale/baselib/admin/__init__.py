from JumpScale import j
j.base.loader.makeAvailable(j, 'tools')

def cb():
    from .Admin import AdminFactory
    return AdminFactory()

j.tools._register('admin', cb)
