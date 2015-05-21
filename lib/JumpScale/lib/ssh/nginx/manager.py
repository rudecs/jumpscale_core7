

class NginxManagerFactory(object):
    def get(self, con):
        return NginxManager(con)


class NginxManager(object):
    def __init__(self, con):
        self._con = con
