from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')
from .ObjectInspector import ObjectInspector
j.tools.objectinspector=ObjectInspector()
