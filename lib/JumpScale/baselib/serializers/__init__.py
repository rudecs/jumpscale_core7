from JumpScale import j

def cb():
    from .SerializersFactory import SerializersFactory
    return SerializersFactory()

j.base.loader.makeAvailable(j, 'db')
j.db._register('serializers', cb)
