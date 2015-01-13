from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')
from .PackInCode import *
j.tools.packInCode=packInCodeFactory()
