from JumpScale import j
import ujson

class AUTH(object):

    def load(self,osis):
        pass

    def authenticate(self,osis,method,user,passwd, session):
        if j.core.osis.cmds._authenticateAdmin(user=user,passwd=passwd):
            return True
        return False
