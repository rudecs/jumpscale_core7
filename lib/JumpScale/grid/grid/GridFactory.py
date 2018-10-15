from JumpScale import j

# from CoreModel.ModelObject import ModelObject
import JumpScale.grid.osis
#from ZBrokerClient import ZBrokerClient
from collections import namedtuple
import JumpScale.grid.geventws
from  JumpScale.grid.gridhealthchecker.gridhealthchecker import GridHealthChecker
import time


# class ZCoreModelsFactory():

#     def getModelObject(self, ddict={}):
#         return ModelObject(ddict)


class GridFactory():

    def __init__(self):
        self.brokerClient = None
        # self.zobjects = ZCoreModelsFactory()
        self.id = None
        self.nid=None
        self.config = None
        self.roles = list()
        self._healthchecker = None
    
    @property
    def healthchecker(self):
        if not self._healthchecker:
            self._healthchecker = GridHealthChecker()
        return self._healthchecker

    def _loadConfig(self,test=True):
        if "config" not in j.application.__dict__:
            raise RuntimeWarning("Grid/Broker is not configured please run configureBroker/configureNode first and restart jshell")
        self.config = j.application.config

        if self.config == None:
            raise RuntimeWarning("Grid/Broker is not configured please run configureBroker/configureNode first and restart jshell")

        self.id = j.application.whoAmI.gid
        self.nid = j.application.whoAmI.nid

        if test:

            if self.id == 0:
                j.errorconditionhandler.raiseInputError(msgpub="Grid needs grid id to be filled in in grid config file", message="", category="", die=True)

            if self.nid == 0:
                j.errorconditionhandler.raiseInputError(msgpub="Grid needs grid node id (grid.nid) to be filled in in grid config file", message="", category="", die=True)


    def init(self,description="",instance=1):
        self._loadConfig(test=False)

        roles = j.application.config['grid']['node']['roles']
        roles = [ role.lower() for role in roles ]
        self.roles = roles
        j.logger.consoleloglevel = 5

    def getLocalIPAccessibleByGridMaster(self):
        return j.system.net.getReachableIpAddress(self.config.get("grid.master.ip"), 5544)

    def isGridMasterLocal(self):
        broker = self.config.get("grid.master.ip")
        return j.system.net.isIpLocal(broker)
