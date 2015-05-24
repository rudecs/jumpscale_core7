from fabric.api import settings
import functools

EXPOSED_FIELDS = [
    'authentication',
    'logpid',
    'fscharset',
    'clientcharset',
    'trustedgid',
    'maxclientsnumber',
    'maxclientsperip',
    'syslogfacility',
    'fortunesfile',
    'pidfile',
    'maxidletime',
    'maxdiskusagepct',
    'login',
    'limitrecursion',
    'maxload',
    'natmode',
    'uploadscript',
    'altlog',
    'passiveportrange',
    'forcepassiveip',
    'anonymousratio',
    'userratio',
    'autorename',
    'antiwarez',
    'bind',
    'anonymousbandwidth',
    'userbandwidth',
    'minuid',
    'umask',
    'bonjour',
    'trustedip',
    'peruserlimits',
    'customerproof'
]

EXPOSED_BOOLEAN_FIELDS = [
    'enabled',
    'notruncate',
    'ipv4only',
    'ipv6only',
    'chrooteveryone',
    'brokenclientscompatibility',
    'daemonize',
    'verboselog',
    'displaydotfiles',
    'anonymousonly',
    'noanonymous',
    'norename',
    'dontresolve',
    'anonymouscantupload',
    'createhomedir',
    'keepallfiles',
    'anonymouscancreatedirs',
    'nochmod',
    'allowuserfxp',
    'allowanonymousfxp',
    'prohibitdotfileswrite',
    'prohibitdotfilesread',
    'allowdotfiles',
]


class PureFTPError(Exception):
    pass


class PureFTP(object):
    PACKAGE = 'pure-ftpd'
    SECTION = 'pure-ftpd'

    def __new__(cls, *args, **kwargs):
        for field in EXPOSED_FIELDS:
            prop = property(
                functools.partial(cls._get, field=field),
                functools.partial(cls._set, field=field)
            )

            setattr(cls, field, prop)

        for field in EXPOSED_BOOLEAN_FIELDS:
            prop = property(
                functools.partial(cls._getb, field=field),
                functools.partial(cls._set, field=field)
            )
            setattr(cls, field, prop)

        return super(PureFTP, cls).__new__(cls, *args, **kwargs)

    def __init__(self, wrt):
        self._wrt = wrt
        self._package = None

    def _get(self, field):
        return self.section.get(field)

    def _getb(self, field):
        return self.section.getBool(field, True)

    def _set(self, value, field):
        self.section[field] = value

    @property
    def package(self):
        if self._package is None:
            self._package = self._wrt.get(PureFTP.PACKAGE)

        return self._package

    @property
    def section(self):
        sections = self.package.find(PureFTP.SECTION)
        if not sections:
            section = self.package.add(PureFTP.SECTION)
        else:
            section = sections[0]

        return section

    def commit(self):
        self._wrt.commit(self.package)
        con = self._wrt.connection
        with settings(shell=self._wrt.WRT_SHELL, warn_only=not self.enabled,
                      abort_exception=PureFTPError):
            # restart ftp
            con.run('/etc/init.d/pure-ftpd restart')
