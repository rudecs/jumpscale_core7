from JumpScale import j

from .System import System
from .text import Text
j.system=System()

j.base.loader.makeAvailable(j, 'tools')
j.tools.text = Text


