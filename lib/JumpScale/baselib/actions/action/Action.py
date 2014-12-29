import ujson as json
from JumpScale import j
import time

class Action:    
    def __init__(self, description="", cmds="",action=None,actionRecover=None,actionArgs={},category="unknown",name="unknown",\
        errorMessage="", resolutionMessage="", loglevel=1,die=True,stdOutput=False,errorOutput=True,retry=1,jp=None):
        '''
        @param id is unique id which allows finding back of action
        @param description: Action description (what are we doing)
        @param errorMessage: message to give when error
        @param resolutionMessage: Action resolution message (how to resolve the action when error)
        @param show: Display action
        @param loglevel: Message level
        @param action: python function to execute
        @param actionRecover: python function to execute when error
        @param actionArgs is dict with arguments
        @param cmds is list of commands to execute on os
        @param state : INIT,RUNNING,OK,ERROR
        @param jp: jpackage, will be used to get category filled in
        '''
        self.category=category
        if self.category=="unknown" and jp<>None:
            self.category="jp_%s_%s"%(jp.jp.domain,jp.jp.name)
        self.jp=jp
        self.name=name
        self.action=action
        self.actionRecover=actionRecover
        self.actionArgs=actionArgs
        self.description = description
        self.resolutionMessage = resolutionMessage
        self.errorMessage = errorMessage
        self.loglevel = loglevel
        self.state="INIT"
        self.retry=retry
        self.stdOutput=stdOutput
        self.errorOutput=errorOutput
        self.die=die
        self.cmds=cmds

    # def save(self):
    #     ddict=copy.copy(self.__dict__)
    #     ddict.pop

    def execute(self):        
        print "* %-20s: %-15s %s"%(self.category,self.name,self.description)
        if self.stdOutput==False:
            j.console.hideOutput()
        rcode=0
        output=""
        for i in range(self.retry+1):
            if self.action<>None:
                try:
                    output=self.action(**self.actionArgs)
                except Exception,e:
                    if self.retry>1 and i<self.retry:
                        time.sleep(0.1)
                        print "  RETRY, ERROR (%s/%s)"%(i+1,self.retry)
                        continue
                    rcode=1
                    output=e
                break
            else:
                if self.cmds<>"":
                    # rcode,output,err=j.do.execute(self.cmds, outputStdout=self.stdOutput, outputStderr=self.stdOutput, useShell=True, log=True, cwd=None, timeout=600, captureout=True, dieOnNonZeroExitCode=False)
                    # output+=err
                    rcode,output=j.system.process.execute(self.cmds, dieOnNonZeroExitCode=False, outputToStdout=self.stdOutput or self.errorOutput, useShell=False)
                    if rcode>0 and self.retry>1 and i<self.retry:
                        time.sleep(0.1)
                        print "  RETRY, ERROR (%s/%s)"%(i+1,self.retry)
                        continue                     
                break
        
        j.console.enableOutput()
        if rcode>0:         
            j.console.showOutput()
            self.state="ERROR"
            if self.actionRecover!=None:
                self.actionRecover(**actionArgs)
            
            if self.die:
                j.events.inputerror_critical(self.geterrmsg(output),"%s.%s"%(self.category,self.name))
            else:
                if self.errorOutput:
                    "INTERNAL ERROR WAS:\n%s"%output
                    print(self.geterrmsg())
        else:
            self.state="OK"


        return rcode,output

    def geterrmsg(self,output=""):
        msg= "ERROR FOR ACTION: %s\%s\n"%(self.category,self.name)
        if self.errorMessage!="":
            msg+= self.errorMessage
        if self.resolutionMessage!="":
            msg+= "RESOLVE:\n"
            msg+= "%s\n"%self.resolutionMessage
        if output!="":
            msg+="\nOUTPUT WAS:\n%s"%output
        return msg




