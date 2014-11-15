
__all__ = ['Time','IDgenerator', ]

from JumpScale import j

from JumpScale.core.base.time.Time import Time
from JumpScale.core.base.idgenerator.IDGenerator import IDGenerator

class Empty():
    pass

if not j.__dict__.has_key("base"):
    j.base=Empty()

    
j.base.time=Time()
j.base.idgenerator=IDGenerator()