
#import sys
#import inspect
#import textwrap
#import operator
import string

from JumpScale import j

class Transaction(object):
    '''
    Representation of an transaction
    @property errorcallback: std None, is function which will be called when error happens in this transaction
    @property logs : logs captured since start of transaction
    

    '''
    def __init__(self, description, errormessage, resolutionmessage, callback=None, \
                 callbackparams=None, maxloglevel=2,maxloglevelcapture=5,silent=False):
        '''Initialize a new transaction

        @param description: Description message displayed to the user
        @param errormessage: Error message displayed when the transaction fails
        @param resolutionmessage: Resolution message displayed when the transaction fails
        @param maxloglevel, is max log level which will be remembered
        @param callback can use this to provide a sort of rollback mechanism to e.g. cleanup a state        
        @param callbackparams dict of parameters
        '''
        self.description = description or ''
        self.errormessage = errormessage or ''
        self.resolutionmessage = resolutionmessage or ''
        self.maxloglevel=maxloglevel
        self.maxloglevelcapture=maxloglevelcapture
        self.callback=callback
        self.callbackparams=callbackparams
        self.logs=[]#remember all log messages with loglevel < maxloglevel
        self.silent=silent
        
    def getLog(self,maxLevel=9):
        msg=""
        for log in self.log:
            logstr=str(log)
            msg+=j.console.formatMessage(logstr,withStar=True)
        return msg
        
    def __str__(self):
        dictionary={"descr":self.description,"errmsg":self.errormessage,\
                                               "resolmsg":self.resolutionmessage}        
        msg=""
        for key in list(dictionary.keys()):
            msg+=j.console.formatMessage(str(dictionary[key]),key,withStar=True)+"\n"
        return msg
     
    def getErrorMessage(self,withloginfo=False):
        msg="Transaction %s failed.\n%s\n%s\n" % (self.description,self.errormessage,self.resolutionmessage)
        if withloginfo:
            msg="\n\n%s%s"%(msg,string.join([log._strshort() for log in self.logs],"\n"))
        return msg
        
    def __repr__(self):
        return self.__str__()
        

