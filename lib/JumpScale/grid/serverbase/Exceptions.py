from JumpScale import j
from JumpScale.core.errorhandling.ErrorConditionHandler import BaseException
import traceback

class AuthenticationError(BaseException):
    pass

class MethodNotFoundException(BaseException):
    pass

class RemoteException(BaseException):
    def __init__(self, message="", eco=None):
        self.message = message
        backtrace = traceback.format_stack()[:-1]
        eco['backtrace'] = """
Remote Backtrace
-----------------

%s

================

Client BackTrace
-----------------

%s

""" % (eco['backtrace'], ''.join(backtrace))
        self.eco = j.errorconditionhandler.getErrorConditionObject(eco)


class LockException(BaseException):
    pass
