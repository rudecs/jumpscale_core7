from JumpScale import j

def cb():
    from .ActionController import ActionController
    return ActionController()

j._register('actions', cb)



