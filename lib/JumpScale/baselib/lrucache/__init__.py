from JumpScale import j
from .LRUCacheFactory import LRUCacheFactory

class Empty():
	pass
if "db" not in j.__dict__:
    j.db=Empty()

j.db.cache=LRUCacheFactory()


