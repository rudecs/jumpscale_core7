from JumpScale import j

def cb():
    from .CodeGenerator import CodeGenerator
    return CodeGenerator()

j.base.loader.makeAvailable(j, 'core')
j.core._register('codegenerator', cb)
