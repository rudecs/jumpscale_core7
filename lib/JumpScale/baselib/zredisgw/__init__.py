from JumpScale import j

def cb():
    from .ZRedisGWFactory import ZRedisGWFactory
    return ZRedisGWFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('zredisgw', cb)

