from JumpScale import j

class system_errorconditionhandler(j.code.classGetBase()):

    """
    errorcondition handling
    
    """

    def __init__(self):

        self._te = {}
        self.actorname = "errorconditionhandler"
        self.appname = "system"

        pass

    def describeCategory(self, category, language, description, resolution_user, resolution_ops, **args):
        """
        describe the errorcondition category (type)
        describe it as well as the possible solution
        is sorted per language
        param:category in dot notation e.g. pmachine.memfull
        param:language language id e.g. UK,US,NL,FR  (
        param:description describe this errorcondition category
        param:resolution_user describe this errorcondition solution that the user can do himself
        param:resolution_ops describe this errorcondition solution that the operator can do himself to try and recover from the situation
        result bool 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method describeCategory")

    def getEcoKey(self, eco):
        key = eco.actorname + str(eco.level) + eco.appname +\
            eco.category + eco.description + eco.tags +\
            eco.descriptionpub
        key = j.base.byteprocessor.hashMd5(key)
        print("ecokey:%s" % key)
        return key

    def processECO(self, eco):
        """
        process eco 
        first find duplicates for eco (errorcondition obj of style as used in this actor)
        the store in db
        """
        key = self.getEcoKey(eco)
        if self.dbmem.cacheExists(key):
            # previous item found
            if eco.lasttime < j.base.time.getTimeEpoch() - 3600:
                self.dbmem.cacheDelete(key)
            else:
                # we found a duplicate and it is not expired
                eco2 = self.dbmem.cacheGet(key)
                self.model_errorcondition_set(eco2)  # @todo does not work yet test @todo hendrik
                # from pylabs.Shell import ipshellDebug,ipshell
                # print "DEBUG NOW double eco"
                # ipshell()

                return eco2

        else:
            # no previous found
            self.dbmem.cacheSet(key, eco, expirationInSecondsFromNow=3600)
            return self.model_errorcondition_set(eco)
