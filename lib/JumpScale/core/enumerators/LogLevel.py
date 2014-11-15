
from JumpScale.core.baseclasses import BaseEnumeration


class LogLevel(BaseEnumeration):
    """
    Iterrator for levels of log
    1: end user message
    2: operator message
    3: stdout
    4: stderr
    5: tracing 1 and/or backtrace python
    6: tracing 2
    7: tracing 3
    8: tracing 4
    9: tracing 5
    10: special level, is the marker level    
    """    
    def __init__(self, level):
        self.level = level

    def __int__(self):
        return self.level
    
    def __cmp__(self, other):
        return cmp(int(self), int(other))


LogLevel.registerItem('unknown', 0)
LogLevel.registerItem('endusermsg', 1)
LogLevel.registerItem('operatormsg', 2)
LogLevel.registerItem('stdout', 3)
LogLevel.registerItem('stderr', 4)
LogLevel.registerItem('tracing1', 5)
LogLevel.registerItem('tracing2', 6)
LogLevel.registerItem('tracing3', 7)
LogLevel.registerItem('tracing4', 8)
LogLevel.registerItem('tracing5', 9)
LogLevel.registerItem('marker', 10)

LogLevel.finishItemRegistration()


