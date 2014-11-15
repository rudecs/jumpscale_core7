from JumpScale import j
from .CodeTools import CodeTools
from .CodeManager import CodeManager
# j.base.loader.makeAvailable(j, '')
j.base.loader.makeAvailable(j, 'codetools')
j.codetools = CodeTools()
j.codetools.codemanager = CodeManager()
