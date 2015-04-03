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
        # TODO, should take in account the domain too
        services = j.atyourservice.findServices(name=self.name,instance=instance)
        if len(services)>0:
            j.events.opserror_critical("service %s__%s__%s already exists"%(self.domain,self.name,instance))
        service = Service(instance=instance,servicetemplate=self,args=args,parent=parent)
        return service

    def getInstance(self,instance=None):
        """
        get first installed or main
        """
        if instance is None:
            instances = self.listInstances()
            if instances:
                instance = instances[0]
            else:
                instance = 'main'
        services =  j.atyourservice.findServices(domain=self.domain,name=self.name,instance=instance)
        if len(services) <= 0:
            j.events.opserror_critical("no instance found for %s__%s__%s"%(self.domain,self.name,instance))
        return services[0]

    def existsInstance(self,instance):
        if instance == "" or instance == None:
            j.events.opserror_critical("instance can't be empty")

        services =  j.atyourservice.findServices(domain=self.domain,name=self.name,instance=instance)
        if len(services) > 0:
            return True
        else:
            return False

    def listInstances(self):
        return j.atyourservice.findServices(domain=self.domain,name=self.name)


    def install(self, instance="main",start=True,deps=True, reinstall=False, args={}, parent=None):
        """
        Install Service.

        Default instance = main

        Keyword arguments:
        start     -- whether Service should start after install (default True)
        deps      -- install the Service dependencies (default True)
        reinstall -- reinstall if already installed (default False)
        args      -- arguments to be used when installing
        parent    -- optional service which is mother e.g. install an app in a node.
        """

        service=self.newInstance(instance=instance, args=args ,parent=parent)
        service.install(self, start=start,deps=deps, reinstall=reinstall)



    def __repr__(self):
        return "%-15s:%s"%(self.domain,self.name)

    def __str__(self):
        return self.__repr__()

