from JumpScale import j

def cb():
    from .HashTool import HashTool
    return HashTool()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('hash', cb)
