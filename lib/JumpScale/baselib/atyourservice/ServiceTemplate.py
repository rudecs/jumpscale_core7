from JumpScale import j
import imp
import sys

import JumpScale.baselib.actions
import JumpScale.baselib.packInCode
import JumpScale.baselib.remote.cuisine
from .Service import *
from .RemoteService import RemoteService

def log(msg, level=1):
    j.logger.log(msg, level=level, category='JSERVICE')

class ServiceTemplate(object):

    def __init__(self, domain, name, path, parent):
        self.name = name
        self.domain = domain
        self.hrd = None
        self.parent = parent
        self.metapath = path

    def newInstance(self,instance="main", args={}, hrddata={}, path='', parent=None, precise=False, hrdSeed=None):
        # TODO, should take in account the domain too
        services = j.atyourservice.findServices(name=self.name, instance=instance, parent=parent, precise=precise)
        if len(services)>0:
            if j.application.debug:
                print "Service %s__%s__%s already exists" % (self.domain,self.name,instance)
                print "No creation, just retrieve existing service"
            return services[0]
        fullpath = path or ('%s/domain__name__instance' % parent.path if parent else '')
        remote = [p for p in j.atyourservice.findParents(path=fullpath) if 'node' in p.categories]
        if remote:
            remote = remote[-1]
            service = RemoteService(instance=instance, servicetemplate=self, args=args, path=path, parent=parent,
                                    remotecategory='node', remoteinstance=remote.instance)
        else:
            service = Service(instance=instance, servicetemplate=self, args=args, path=path, parent=parent, hrdSeed=hrdSeed)
        return service

    def getHRD(self):
        if self.hrd ==None:
            self.hrd=j.core.hrd.get(j.system.fs.joinPaths(self.metapath,"service.hrd"))
        return self.hrd

    def getInstanceHRD(self):
        # Gets instance HRDs as string. ASKs are non-interactive in this case
        instancehrd = ''
        instancehrdpath = j.system.fs.joinPaths(self.metapath, "instance.hrd")
        if j.system.fs.exists(instancehrdpath):
            instancehrd = j.system.fs.fileGetContents(instancehrdpath)
        return instancehrd

    def getInstance(self, instance=None, parent=None):
        """
        get first installed or main
        """
        if instance is None:
            instances = self.listInstances()
            if instances:
                instance = instances[0]
            else:
                instance = 'main'
        services = j.atyourservice.findServices(domain=self.domain, name=self.name, instance=instance, parent=parent)
        if len(services) <= 0:
            j.events.opserror_critical("no instance found for %s__%s__%s" % (self.domain, self.name, instance))
        return services[0]

    def existsInstance(self, instance, parent=None):
        if instance == "" or instance is None:
            j.events.opserror_critical("instance can't be empty")

        services = j.atyourservice.findServices(domain=self.domain, name=self.name, instance=instance, parent=parent)
        if len(services) > 0:
            return True
        else:
            return False

    def listInstances(self):
        """
        return a list of instance name for this template
        """
        services = j.atyourservice.findServices(domain=self.domain,name=self.name)
        return [service.instance for service in services]

    def install(self, instance="main",start=True,deps=True, reinstall=False, args={}, parent=None, noremote=False, hrdSeed=None):
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

        #check if this platform is supported
        hrd=self.getHRD()
        support=False
        myplatforms=j.system.platformtype.getMyRelevantPlatforms()
        supported=hrd.getList("platform.supported",default=[])
        if supported==[]:
            support=True
        for supportcheck in supported:
            if supportcheck in myplatforms:
                support=True

        if support==False:
            j.events.opserror_critical("Cannot install %s__%s because unsupported platform." % (self.domain, self.name))

        service = self.newInstance(instance=instance, args=args, parent=parent, precise=True, hrdSeed=hrdSeed)
        service.args.update(args)
        service.noremote = noremote
        service.install(start=start, deps=deps, reinstall=reinstall)

    def __repr__(self):
        return "%-15s:%s" % (self.domain, self.name)

    def __str__(self):
        return self.__repr__()
