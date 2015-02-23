from JumpScale import j

def cb():
    from .PackInCode import packInCodeFactory
    return packInCodeFactory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('packInCode', cb)
