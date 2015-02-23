from JumpScale import j

def cb():
    from .Tmux import Tmux
    return Tmux()

j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform._register('screen', cb)
