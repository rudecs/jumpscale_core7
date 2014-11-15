from JumpScale import j
from .Tmux import Tmux
j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform.screen = Tmux()
