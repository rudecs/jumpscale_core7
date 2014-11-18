from JumpScale import j

from .ClassBase import ClassBase

class Appserver6GreenletTaskletsBase(ClassBase):    
    def __init__(self,taskletsPath):
        self.actor=""
        self.method=""
        self.description=""                
        self.server=None #is link to app server which will serve this greenlet, not to be filled in by coder
        self.paramvalidation={}#$paramvalidation
        self.paramdefault={}
        self.paramdescription={}#$paramdescr
        self.paramoptional={}
        self.taskletsPath=taskletsPath
        self.service=""#service object (e.g. the appobject) we want to give to tasklets
        self.te=j.core.taskletengine.get(self.taskletsPath)
        
    def wscall(self,ctx,server):
        params=self.te.execute(ctx.params,service=self.service,job=None,tags=None)
        return params.result        

