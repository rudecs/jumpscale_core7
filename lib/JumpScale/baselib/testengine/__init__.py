from JumpScale import j

def cb():
    from .TestEngine import TestEngine
    return TestEngine()

#from .TestEngineKds import TestEngineKds
#j.tools.testengineKds = TestEngineKds()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('testengine', cb)
