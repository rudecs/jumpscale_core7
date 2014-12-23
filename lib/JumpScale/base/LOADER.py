from JumpScale import j

class Dummy(object):
    def __getattr__(self, key):
        raise AttributeError("%s is not loaded, did your forget an import?" % key)

class Loader(object):
    def makeAvailable(self, obj, path):
        """
        Make sure a path under a object is available
        """
        ob = obj
        for part in path.split('.'):
            if not hasattr(ob, part):
                setattr(ob, part, Dummy())
            ob = getattr(ob, part)



j.base.loader = Loader()
