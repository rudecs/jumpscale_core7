from JumpScale import j

def cb():
    from .CodeTools import CodeTools
    return CodeTools()

j._register('codetools', cb)
