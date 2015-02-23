from JumpScale import j

def cb():
    from .PuppetTool import PuppetTool
    return PuppetTool()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('puppet', cb)
