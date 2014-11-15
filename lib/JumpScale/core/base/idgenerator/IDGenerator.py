
from JumpScale import j
import random


class IDGenerator:
    """
    generic provider of id's
    lives at j.idgenerator
    """

    def generateRandomInt(self,fromInt,toInt):
        """
        how to use:  j.base.idgenerator.generateRandomInt(0,10)
        """
        return random.randint(fromInt,toInt)
        
    def generateIncrID(self,incrTypeId,service,reset=False):
        """
        type is like agent, job, jobstep
        needs to be a unique type, can only work if application service is known
        how to use:  j.base.idgenerator.generateIncrID("agent")
        @reset if True means restart from 1
        """
        key="incrementor_%s"%incrTypeId
        if service.db.exists(key) and reset==False:
            lastid=int(service.db.get(key))
            service.db.testAndSet(key,str(lastid),str(lastid+1))
            return lastid+1
        else:
            service.db.set(key,"1")
            return 1
    
    def getID(self,incrTypeId,objectUniqueSeedInfo,service,reset=False):
        """
        get a unique id for an object uniquely identified
        remembers previously given id's
        """
        key="idint_%s_%s" % (incrTypeId,objectUniqueSeedInfo)
        if service.db.exists(key) and reset==False:
            id=int(service.db.get(key))
            return id
        else:
            id=self.generateIncrID(incrTypeId,service)            
            service.db.set(key,str(id))
            return id
        
    def generateGUID(self):
        """
        generate unique guid
        how to use:  j.base.idgenerator.generateGUID()
        """
        import uuid
        return str(uuid.uuid4())