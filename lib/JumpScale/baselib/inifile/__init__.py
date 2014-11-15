from JumpScale import j
from .IniFile import InifileTool
j.base.loader.makeAvailable(j, 'tools')
j.tools.inifile = InifileTool()
