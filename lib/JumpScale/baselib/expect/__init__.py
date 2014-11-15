from JumpScale import j
from .Expect import ExpectTool

j.base.loader.makeAvailable(j, 'tools')

j.tools.expect=ExpectTool()
