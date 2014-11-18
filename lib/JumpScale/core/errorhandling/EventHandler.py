from JumpScale import j

class EventHandler(object):

    def bug_critical(self,msg,category="",jobid=0,e=None):
        """
        will die
        @param e is python error object when doing except
        """        
        if e!=None:
            msg+="\nERROR:%s\n"%e
        if jobid!=0:
            msg+="((C:%s L:1 T:B J:%s))"%(category,jobid)
        else:
            msg+="((C:%s L:1 T:B))"%category

        j.errorconditionhandler.raiseCritical(msg,category=category, pythonExceptionObject=e,die=False)
        # raise RuntimeError(msg)

    def bug_warning(self,msg,category="",e=None):
        """
        will die
        @param e is python error object when doing except
        """        
        if e!=None:
            msg+="\nERROR:%s\n"%e
        msg+="((C:%s L:1 T:W))"%category
        j.errorconditionhandler.raiseWarning(msg,category=category, pythonExceptionObject=e)

    def opserror_critical(self,msg,category=""):
        """
        will die
        """    
        msg2=""
        #     msg2+="((C:%s L:1 T:O))"%category
        j.errorconditionhandler.raiseOperationalCritical(msg, category=category)
        # raise RuntimeError(msg)

    def opserror(self,msg,category="",e=None):
        """
        will NOT die
        will make warning event is the same as opserror_warning
        @param e is python error object when doing except
        """        
        if e!=None:
            msg+="\nERROR:%s\n"%e
        j.errorconditionhandler.raiseOperationalWarning(msg,category=category)


    def inputerror_critical(self,msg,category="",msgpub=""):
        """
        will die
        """    
        j.errorconditionhandler.raiseInputError(message=msg, category=category,msgpub=msgpub,die=True ,backtrace="",tags="")

    def inputerror_warning(self,msg,category="",msgpub=""):
        """
        will die
        """    
        j.errorconditionhandler.raiseInputError(message=msg, category=category,msgpub=msgpub,die=False ,backtrace="",tags="")


    opserror_warning = opserror

