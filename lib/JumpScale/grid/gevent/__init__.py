from JumpScale import j

def cb():
    from .GeventLoopFactory import GeventLoopFactory
    return GeventLoopFactory()

j.base.loader.makeAvailable(j, 'core')
j.core._register('gevent', cb)
