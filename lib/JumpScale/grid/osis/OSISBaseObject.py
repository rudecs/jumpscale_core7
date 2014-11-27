from JumpScale import j
import JumpScale.baselib.hash

from .OSISBaseObjectComplexType import OSISBaseObjectComplexType

class OSISBaseObject(OSISBaseObjectComplexType):

    def __init__(self, ddict=None, **kwargs):
        if ddict:
            kwargs = ddict
        for key, value in list(kwargs.items()):
            setattr(self, key, value)

    def load(self, ddict):
        """
        update object from ddict being given
        """
        self.__dict__.update(ddict)

    def __str__(self):
        return j.code.object2json(self,True)
                
    __repr__=__str__
        
