from JumpScale import j

def cb():
    from .FabricTool import FabricTool
    return FabricTool()

j.base.loader.makeAvailable(j, 'tools')
j.remote._register('fabric', cb)
