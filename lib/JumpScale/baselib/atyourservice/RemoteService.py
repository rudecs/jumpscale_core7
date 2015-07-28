from JumpScale import j
from .Service import Service


def log(msg, level=1):
    j.logger.log(msg, level=level, category='JSREMOTEERVICE')


class RemoteService(Service):

    def __init__(self, domain='', name='', instance='', hrd=None, servicetemplate=None, path="", args=None, parent=None, remotecategory='', remoteinstance=''):
        super(RemoteService, self).__init__(domain=domain, name=name, instance=instance, hrd=hrd, servicetemplate=servicetemplate, path=path, args=args, parent=parent)
        self.hrd.set("producer.%s" % remotecategory, remoteinstance)
        self.hrd.save()
        self.deps = self.getDependencies()

    @property
    def id(self):
        return j.atyourservice.getId(self.domain, self.name, self.instance, self.parent)

    def init(self):
        pass

    def stop(self, deps=True):
        self.actions.executeaction(self, actionname="stop")

    def build(self, deps=True, processed={}):
        self.actions.executeaction(self, actionname="build")

    def start(self, deps=True, processed={}):
        self.actions.executeaction(self, actionname="start")

    def restart(self, deps=True, processed={}):
        self.actions.executeaction(self, actionname="restop")

    def prepare(self, deps=True, reverse=True, processed={}):
        self.actions.executeaction(self, actionname="prepare")

    def install(self, start=True, deps=True, reinstall=False, processed={}):
        """
        Install Service.

        Keyword arguments:
        start     -- whether Service should start after install (default True)
        deps      -- install the Service dependencies (default True)
        reinstall -- reinstall if already installed (default False)
        """
        self.actions.executeaction(self, actionname="install")

    def publish(self, deps=True, processed={}):
        """
        check which repo's are used & push the info
        this does not use the build repo's
        """
        self.actions.executeaction(self, actionname="publish")

    def package(self, deps=True, processed={}):
        """
        """
        self.actions.executeaction(self, actionname="package")

    def update(self, deps=True, processed={}):
        """
        - go over all related repo's & do an update
        - copy the files again
        - restart the app
        """
        self.actions.executeaction(self, actionname="update")

    def resetstate(self, deps=True, processed={}):
        """
        remove state of a service.
        """
        self.actions.executeaction(self, actionname="resetstate")

    def reset(self, deps=True, processed={}):
        """
        - remove build repo's !!!
        - remove state of the app (same as resetstate) in jumpscale (the configuration info)
        - remove data of the app
        """
        self.actions.executeaction(self, actionname="reset")

    def removedata(self, deps=False, processed={}):
        """
        - remove build repo's !!!
        - remove state of the app (same as resetstate) in jumpscale (the configuration info)
        - remove data of the app
        """
        self.actions.executeaction(self, actionname="removedata")

    def execute(self, cmd=None, deps=False, processed={}):
        """
        execute cmd on service
        """
        self.actions.executeaction(self, actionname="cmd", cmd=self.cmd)

    def uninstall(self, deps=True, processed={}):
        self.actions.executeaction(self, actionname="uninstall")

    def monitor(self, deps=True, processed={}):
        """
        do all monitor checks and return True if they all succeed
        """
        self.actions.executeaction(self, actionname="monitor")

    def iimport(self, url, deps=True, processed={}):
        self.actions.executeaction(self, actionname="iimport")

    def export(self, url, deps=True, processed={}):
        self.actions.executeaction(self, actionname="export")

    def configure(self, deps=True, restart=True, processed={}):
        self.actions.executeaction(self, actionname="configure")

    def __repr__(self):
        return "%-15s:%-15s:%s" % (self.domain, self.name, self.instance)

    def __str__(self):
        return self.__repr__()
