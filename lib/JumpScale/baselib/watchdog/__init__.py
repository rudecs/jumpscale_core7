from JumpScale import j

class WatchdogEvent:
    def __init__(self,gid=0,nid=0,category="",state="",value=0,ecoguid="",gguid="",ddict={}):
        if ddict<>{}:
            self.__dict__=ddict
        else:
            self.gguid=gguid
            self.nid=nid
            self.gid=gid
            self.category=category
            self.state=state
            self.value=value
            self.ecoguid=""
            self.epoch=j.base.time.getTimeEpoch()
            self.escalationstate=""
            self.escalationepoch=0
            self.message_id=""
            self.log=[]

    def __str__(self):
        dat=j.base.time.epoch2HRDateTime(self.epoch)
        return "%s %s %s %-30s %-10s %s"%(dat,self.gid,self.nid,self.category,self.state,self.value)

    __repr__=__str__


def getHSetKey(gguid):
    return "watchdogevents:%s"%gguid
