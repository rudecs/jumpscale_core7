from JumpScale import j
from ClassBase import ClassBase

class Appserver6GreenletBase(ClassBase):    
    def __init__(self):
        self.actor=""
        self.method=""
        self.description=""                
        self.server=None #is link to app server which will serve this greenlet, not to be filled in by coder
        self.paramvalidation={}#e.g.{"reponame":""}  #dict with regex per param
        self.paramdescription={}  #dict with description per param    
        self.paramoptional={}
        
    def wscall(self,wscontext,server):
        """
        webserver will call this method when user requests the right method
        @params is a dict
        """
        raise NotImplemented()




