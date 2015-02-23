from JumpScale import j

def cb():
    from .IniFile import InifileTool
    return InifileTool()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('inifile', cb)
