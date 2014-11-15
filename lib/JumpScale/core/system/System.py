
'''General system management methods'''


import os, sys, shutil, fnmatch, select, re, subprocess

try:
    import pwd
except:
    if sys.platform.startswith('win'):
        pass
    else:
        raise "python module pwd is not supported on this platform, please fix the dependency"
    
import time,socket,random,tempfile
from JumpScale import j
#from JumpScale.core.Vars import Vars
from JumpScale.core.system.fs import SystemFS
from JumpScale.core.system.string import String
from JumpScale.core.system.net import SystemNet
from JumpScale.core.system.process import SystemProcess

if sys.platform.startswith('win'):
    from JumpScale.core.system.windows import WindowsSystem
else:
    from JumpScale.core.system.unix import UnixSystem

from JumpScale.core.system.fswalker import FSWalker

try:
    from functools import wraps
except ImportError:
    def wraps(f):
        return f

def _wrap_deprecated_fs(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        #By the end of May (says Jochen) this should become
        #raise DeprecationWarning
        j.logger.log('Using deprecated method %s on System' % f.__name__, 5)
        s = SystemFS()
        return f(s, *args, **kwargs)
    return wrapper

def _wrap_deprecated_net(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        #By the end of May (says Jochen) this should become
        #raise DeprecationWarning
        j.logger.log('Using deprecated method %s on System' % f.__name__, 5)
        s = SystemNet()
        return f(s, *args, **kwargs)
    return wrapper

def _wrap_deprecated_process(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        #By the end of May (says Jochen) this should become
        #raise DeprecationWarning
        j.logger.log('Using deprecated method %s on System' % f.__name__, 5)
        s = SystemProcess()
        return f(s, *args, **kwargs)
    return wrapper


class System:
    #jumpscale internal object
    # Singleton state
    __shared_state = {}
    '''Singleton-like shared state
    @type: dict
    '''

    _currentActionDescription=""
    '''Description of the currently running action
    @type: string
    '''

    _currentActionErrorMessage=""
    '''Error message generated by the currently running action

    @type: string
    '''

    _currentActionResolutionMessage=""
    _currentActionStatus=""
    '''Status of the currently running action

    @type: string
    '''

    _currentActionLevel=0
    '''Level of the currently running action

    @type: number
    '''

    _verbosityLevel=2
    '''Verbosity level

    @type: number
    '''

    _jPlatformType=None
    '''PlatformType of currently running platform

    @type: L{jumpscale.enumerators.PlatformType.PlatformType}
    '''

    fswalker = FSWalker
    '''Accessor to FSWalker functionality'''

    # Initialize singleton object
    def __init__(self):
        '''Initializes a new System instance
        Binds currently running L{jumpscale.enumerators.PlatformType.PlatformType}
        and initializes the C{fs}, C{net} and C{process} attributes.
        '''
        self.platformtype=self._jPlatformType
        self.fs = SystemFS()
        self.net = SystemNet()
        self.string=String()
        self.process = SystemProcess()
        if sys.platform.startswith('win'):
            self.windows = WindowsSystem()
        else:
            self.unix = UnixSystem()
            