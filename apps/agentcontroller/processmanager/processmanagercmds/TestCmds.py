from JumpScale import j
import time

class TestCmds():
    ORDER=100

    def __init__(self,daemon=None):
        self._name="tests"
        if not daemon:
            return
        self.daemon=daemon
        self._adminAuth=daemon._adminAuth

    def echoTest(self,msg="",session=None):        
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        return msg

    def raiseTest(self,msg="",session=None):        
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        raise RuntimeError("test error")

    def timeOutTest(self,msg="",session=None):        
        if session<>None:
            self._adminAuth(session.user,session.passwd)        
        time.sleep(60)
        return msg
