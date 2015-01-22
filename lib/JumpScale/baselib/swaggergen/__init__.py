from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')
from .SwaggerGen import *
j.tools.swaggerGen = SwaggerGen()
