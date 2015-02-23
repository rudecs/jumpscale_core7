from JumpScale import j

def cb():
    import JumpScale.baselib.code
    from .OSIS import OSIS
    return OSIS()
j.base.loader.makeAvailable(j, 'core')
j.core._register('osismodel', cb)
