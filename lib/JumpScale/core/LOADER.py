from JumpScale import j
from JumpScale import Loader as DummyLoader


class Loader(object):
    def makeAvailable(self, obj, path):
        """
        Make sure a path under a object is available
        """
        ob = obj
        for part in path.split('.'):
            if not hasattr(ob, part):
                setattr(ob, part, DummyLoader())
            ob = getattr(ob, part)

j.base.loader = Loader()
