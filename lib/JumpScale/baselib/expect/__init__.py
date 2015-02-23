from JumpScale import j

def cb():
    from .Expect import ExpectTool
    return ExpectTool()

j.base.loader.makeAvailable(j, 'tools')

j.tools._register('expect', cb)
