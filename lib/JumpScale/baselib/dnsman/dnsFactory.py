from bind import BindDNS

class DNSFactory(object):
    def __init__(self):
        self.bindObj = None

    @property
    def bind(self):
        if not self.bindObj:
            self.bindObj = BindDNS()
        return self.bindObj