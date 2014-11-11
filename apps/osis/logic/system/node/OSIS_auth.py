from JumpScale import j

class AUTH():

    def __init__(self):
        self.nodeguids = dict()

    def load(self,osis):
        pass

    def authenticate(self,osis,method,user,passwd, session):
        if j.core.osis.cmds._authenticateAdmin(user=user,passwd=passwd,die=False):
            return True
        if user=="node" and method in ["set","get", "auth"]:
            if passwd in self.nodeguids:
                return True
            else:
                nodes = osis.find({'machineguid': passwd}, session=session)[1:]
                if nodes:
                    self.nodeguids[passwd] = nodes[0]['id']
                    return True
        return False
