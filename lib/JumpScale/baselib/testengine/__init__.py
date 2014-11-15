from JumpScale import j
import JumpScale.baselib.params
from .TestEngine import TestEngine
from .TestEngineKds import TestEngineKds

j.base.loader.makeAvailable(j, 'tools')
j.tools.testengine = TestEngine()
j.tools.testengineKds = TestEngineKds()
