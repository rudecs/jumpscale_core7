from JumpScale import j
from .ClassBase import ClassBase

class Appserver6GreenletScheduleBase(ClassBase):    
    def __init__(self):
        self.actor=""
        self.method=""
        self.timeout=60*15
        self.timeoutKill=0
        self.period=0
        self.periodMax=0
        #locks: [["mercurial.pull",""]]  first arg is lockcat, then lock instance id (optional)
        #this is the lock which will be taken
        self.locks=None         
        #lockswait: [["mercurial.pullall",[],60*10],...]  first arg is lockcat, then lock instance id (optional), then timeout before the wait will fail
        self.lockswait=None 
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
        reponame=params["reponame"]
        ##next locks show how to use for one specific lock instance
        #locks=[["mercurial.pullone",[reponame]]]
        #lockswait=[["mercurial.pullall",[],60*10],["mercurial.pullone",[reponame],10*60]]        
        taskid=self.server.schedule(self.taskMethod,{"name":reponame},timeout=self.timeout,timeoutKill=self.timeoutKill,\
                                    locks=self.locks,lockswait=self.lockswait) 
        #asked for async so will get the taskid back
        result={}
        result["resultcode"]=1
        result["taskid"]=taskid
        result["msg"]="a message"
        return result

    def taskMethod(params):           
        """
        method which will be executed by the scheduler, if used
        """
        raise NotImplemented()
        return "return some result, will be returned to the wscall"



