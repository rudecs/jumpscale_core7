from JumpScale import j

OsisBaseObject=j.core.osis.getOsisBaseObjectClass()

class ECO(OsisBaseObject):

    """
    error condition object
    """

    def __init__(self, ddict={},id=0,guid="",errormessage="",errormessagePub="",level=1,category="",tags="",transactionsinfo="",\
                    gid=0,nid=0,pid=0,aid=0,jid=0,masterjid=0,epoch=0,type=0):
        if ddict <> {}:
            self.load(ddict)
        else:
            self.errormessage=errormessage
            self.errormessagePub=errormessagePub
            self.level=int(level) #1:critical, 2:warning, 3:info
            self.category=category #dot notation e.g. machine.start.failed
            self.tags=tags #e.g. machine:2323

            self.code=""
            self.funcname=""
            self.funcfilename=""
            self.funclinenr=0
            self.backtrace=""
            self.backtraceDetailed=""
            self.extra=""

            self.appname=j.application.appname #name as used by application

            self.id=0

            self.gid = gid
            self.nid = nid
            self.aid = aid
            self.pid = pid
            self.jid = jid

            if self.gid==None or self.nid==None:
                raise RuntimeError("cannot create osis object for eco if no gid or nid specified")            

            if not int(self.gid)>0 or not int(self.nid)>0:
                raise RuntimeError("cannot create osis object for eco if no gid or nid specified, needs to be bigger than 0.")            

            self.masterjid = masterjid

            if epoch==0:
                self.epoch= j.base.time.getTimeEpoch()
            else:
                self.epoch=epoch

            self.type=str(type)

            self.state="NEW" #["NEW","ALERT","CLOSED"]

            self.lasttime=0 #last time there was an error condition linked to this alert
            self.closetime=0  #alert is closed, no longer active

            self.occurrences=1 #nr of times this error condition happened
       

    def getUniqueKey(self):
        """
        return unique key for object, is used to define unique id
        """
        if self.category<>"":
            C= "%s_%s_%s_%s_%s_%s_%s_%s"%(self.gid,self.nid,self.category,self.level,self.funcname,self.funcfilename,self.appname,self.type)
        else:
            C= "%s_%s_%s_%s_%s_%s_%s_%s"%(self.gid,self.nid,self.errormessage,self.level,self.funcname,self.funcfilename,self.appname,self.type)
        return j.tools.hash.md5_string(C)

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        if not self.guid:
            self.gid = int(self.gid)
            self.id = int(self.id)
            self.guid = "%s_%s_%s" % (self.gid, self.nid,self.id)
        return self.guid

