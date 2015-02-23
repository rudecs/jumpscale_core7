from JumpScale import j

def cb():
    from .ObjectInspector import ObjectInspector
    return ObjectInspector()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('objectinspector', cb)
