from JumpScale import j

def cb():
    from .SwaggerGen import SwaggerGen
    return SwaggerGen()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('swaggerGen', cb)
