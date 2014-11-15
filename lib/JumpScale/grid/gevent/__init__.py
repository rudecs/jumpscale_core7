from JumpScale import j
from .GeventLoopFactory import GeventLoopFactory
j.base.loader.makeAvailable(j, 'core')
j.core.gevent = GeventLoopFactory()
