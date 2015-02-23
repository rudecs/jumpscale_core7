from JumpScale import j
import imp
import sys

import JumpScale.baselib.actions
import JumpScale.baselib.packInCode
import JumpScale.baselib.remote.cuisine
from .Service import *

def log(msg, level=1):
    j.logger.log(msg, level=level, category='JSERVICE')

class ServiceTemplate():

    def __init__(self,domain,name,path):
        self.name=name
        self.domain=domain
        self.hrd=None
        self.metapath=path        

    def newInstance(self,instance="main", args={}, hrddata=None,parent=None):
        return Service(instance=instance,servicetemplate=self,args=args, hrddata=hrddata,parent=parent)

    def getInstance(self,instance=None):
        # get first installed or main
        if instance is None:
            instances = self.listInstances(node=node)
            if instances:
                instance = instances[0]
            else:
                instance = 'main'
        return j.atyourservice.find(domain=self.domain,name=self.name,maxnr=1,instance=instance)[0]

    def existsInstance(self,instance):
        res=j.atyourservice.find(domain=self.domain,name=self.name,maxnr=1,instance=instance)
        if res!=[]:
            return True
        else:
            return False

    def listInstances(self):
        res=[]

        from IPython import embed
        print "DEBUG NOW listInstances"
        embed()
        

    def install(self, instance="main",start=True,deps=True, reinstall=False,args={},hrddata=None,parent=None):
        """
        Install Service.
        
        Keyword arguments:
        start     -- whether Service should start after install (default True)
        deps      -- install the Service dependencies (default True)
        reinstall -- reinstall if already installed (default False)
        args      -- arguments to be used when installing
        hrddata   -- predefined configuration items for hrd of service instance
        parent    -- optional service which is mother e.g. install an app in a node.
        """

        service=self.newInstance(instance=instance, args=args, hrddata=hrddata,parent=parent)
        from IPython import embed
        print "DEBUG NOW install service"
        embed()
        


    def __repr__(self):
        return "%-15s:%s"%(self.domain,self.name)

    def __str__(self):
        return self.__repr__()

