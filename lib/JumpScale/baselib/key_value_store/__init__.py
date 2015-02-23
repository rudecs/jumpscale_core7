from JumpScale import j

def cb():
    from .store_factory import KeyValueStoreFactory
    return KeyValueStoreFactory()

j.base.loader.makeAvailable(j, 'db')
j.db._register('keyvaluestore', cb)
