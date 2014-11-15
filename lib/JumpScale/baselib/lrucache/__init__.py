from JumpScale import j
from LRUCacheFactory import LRUCacheFactory

class Empty():
	pass
if not  j.__dict__.has_key("db"):
    j.db=Empty()

j.db.cache=LRUCacheFactory()


