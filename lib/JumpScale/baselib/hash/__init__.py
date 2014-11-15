from JumpScale import j
from .HashTool import HashTool
j.base.loader.makeAvailable(j, 'tools')
j.tools.hash = HashTool()
