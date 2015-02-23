from JumpScale import j

def cb():
    from .CeleryFactory import CeleryFactory
    return CeleryFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('celery', cb)
