from JumpScale import j
from .TaskletEngine import TaskletEngineFactory
import JumpScale.baselib.params

j.base.loader.makeAvailable(j, 'core')
j.core.taskletengine = TaskletEngineFactory()
