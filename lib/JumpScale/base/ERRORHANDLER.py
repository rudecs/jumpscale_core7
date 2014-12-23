from JumpScale import j

import sys
import traceback

class ERRORHANDLER:

    @staticmethod           
    def log(msg):
        print(msg)

    @staticmethod           
    def setExceptHook():
        sys.excepthook = ERRORHANDLER.exceptHook

    @staticmethod
    def exceptHook(ttype, pythonExceptionObject, tb):
        """ 
        every fatal error in jumpscale or by python itself will result in an exception
        in this function the exception is caught.
        This routine will create an errorobject & escalate to the infoserver
        @ttype : is the description of the error
        @tb : can be a python data object or a Event
        """
        
        print("EXCEPTIONHOOK")
        
        ERRORHANDLER.inException=True
           
        #errorobject=self.parsePythonErrorObject(pythonExceptionObject,ttype=ttype,tb=tb)
                        
        #ERRORHANDLER.processErrorConditionObject(errorobject)

        print("**ERROR**")
        print(pythonExceptionObject)
        print("\n".join(traceback.format_tb(tb)))

        # trace=ERRORHANDLER.getTraceback()
        
        ERRORHANDLER.inException=False  

    @staticmethod
    def getTraceback():
        backtrace=""
        stack=""
        for x in traceback.format_stack():
            ignore=False            
            #if x.find("IPython")<>-1 or x.find("MessageHandler")<>-1 \
            #   or x.find("EventHandler")<>-1 or x.find("ErrorconditionObject")<>-1 \
            #   or x.find("traceback.format")<>-1 or x.find("ipython console")<>-1:
            #    ignore=True
            stack = "%s"%(stack+x if not ignore else stack)
            if len(stack)>50:
                backtrace=stack
                return 
        return backtrace


j.base.errorhandler=ERRORHANDLER
