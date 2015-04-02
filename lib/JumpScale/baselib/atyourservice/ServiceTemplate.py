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

    def newInstance(self,instance="main", args={},hrddata={}, parent=None):
        service = Service(instance=instance,servicetemplate=self,args=args,parent=parent)
        # service.log("create instance")
        return service

    def getInstance(self,instance=None, args={},parent=None):
        # get first installed or main
        if instance is None:
            instances = self.listInstances()
            if instances:
                instance = instances[0]
            else:
                instance = 'main'
        # return j.atyourservice.find(domain=self.domain,name=self.name,maxnr=1,instance=instance)[0]
        service = Service(instance=instance,servicetemplate=self, args=args,parent=parent)
        service.init()
        return service

    def existsInstance(self,instance):
        res=j.atyourservice.find(domain=self.domain,name=self.name,maxnr=1,instance=instance)
        if res!=[]:
            return True
        else:
            return False

    def listInstances(self):
        res=[]
        files = j.system.fs.listFilesInDir(j.dirs.hrdDir,recursive=True,filter="%s"%self.name)
        instances = list()
        for path in files:
            from ipdb import set_trace;set_trace()
            name_instance = path.split('/')[-2]
            instances.append()
        return instances


    def install(self, instance="main",start=True,deps=True, reinstall=False, args={}, parent=None):
        """
        Install Service.

        Keyword arguments:
        start     -- whether Service should start after install (default True)
        deps      -- install the Service dependencies (default True)
        reinstall -- reinstall if already installed (default False)
        args      -- arguments to be used when installing
        parent    -- optional service which is mother e.g. install an app in a node.
        """

        service=self.newInstance(instance=instance, args=args ,parent=parent)
        from IPython import embed
        print "DEBUG NOW install service"
        embed()



    def __repr__(self):
        return "%-15s:%s"%(self.domain,self.name)

    def __str__(self):
        return self.__repr__()

