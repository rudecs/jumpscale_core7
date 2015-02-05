from JumpScale import j
from .CodeGenerator import CodeGenerator
j.base.loader.makeAvailable(j, 'core')
j.core.codegenerator = CodeGenerator()
