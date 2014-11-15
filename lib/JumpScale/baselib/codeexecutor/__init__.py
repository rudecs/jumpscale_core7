from JumpScale import j
from .CodeExecutor import CodeExecutor
j.base.loader.makeAvailable(j, '')
j.base.loader.makeAvailable(j, 'codetools.executor')
j.codetools.executor = CodeExecutor()
