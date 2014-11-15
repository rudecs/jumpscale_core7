from JumpScale import j
from .units import Bytes, Sizes
j.base.loader.makeAvailable(j, 'tools.units')
j.tools.units.bytes = Bytes()
j.tools.units.sizes = Sizes()
