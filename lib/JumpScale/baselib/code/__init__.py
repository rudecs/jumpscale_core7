from JumpScale import j

def cb():
    from .Code import Code
    return Code()

j._register('code', cb)
