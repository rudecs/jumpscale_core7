class DNS(object):
    def start(self):
        raise NotImplemented()
        
    def stop(self):
        raise NotImplemented()
    
    def restart(self):
        raise NotImplemented()
    
    def cleanCache(self):
        raise NotImplemented()
    
    def addRecord(self):
        raise NotImplemented()
    
    def deleteRecord(self):
        raise NotImplemented()
    
    def zones(self):
        raise NotImplemented()