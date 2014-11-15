from JumpScale import j
from .store_factory import KeyValueStoreFactory
j.base.loader.makeAvailable(j, 'db')
j.db.keyvaluestore = KeyValueStoreFactory()
