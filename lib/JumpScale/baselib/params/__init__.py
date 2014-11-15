from JumpScale import j
from .Params import ParamsFactory
j.base.loader.makeAvailable(j, 'core')

j.core.params = ParamsFactory()
