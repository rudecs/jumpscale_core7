import sys

from JumpScale import j


def _doNothing(*args, **kwargs):
    '''This function does nothing, used for monkey patching.'''
    pass


class LoggerPatch(object):

    '''
    This logger patch extension changes the log behaviour of Qshell. This is
    done by monkey patching the logger which makes it forward all logging to
    a message server. Note that this patch is automatically applied when the
    extension is loaded. However, it will not if the necessary message server
    isn't available or not running.
    '''

    DEFAULT_ADDRESS = '127.0.0.1:7777'
    CONFIG_PATH = j.system.fs.joinPaths(j.dirs.cfgDir, 'logger_patch.cfg')

    def __init__(self):
        # TODO: Complete documentation.

        self._messageServerClient = None
        self._applied = False
        self.apply()

    def apply(self, *args, **kwargs):
        # TODO: Complete documentation.

        if self._applied:
            print('Logger patch already applied')
            return

        if not hasattr(j.application, 'whoAmIBytestr') or not j.application.whoAmIBytestr:
            j.application.whoAmIBytestr = 12 * '0'  # The whoAmIBytestr should be at least 12 bytes.

        if not j.system.fs.exists(self.CONFIG_PATH):
            print('Logger patch not applied, config not available')
            return

        config = j.tools.inifile.open(self.CONFIG_PATH)

        if not config.checkSection('main')\
                or not config.checkParam('main', 'address'):
            print('Logger patch not applied, config invalid')
            return

        address = config.getValue('main', 'address')

        self._messageServerClient = j.clients.messageserver.get(address)

        # Check if the message server is running by pinging it.
        serverIsRunning = self._messageServerClient.ping()

        if not serverIsRunning:
            print('Logger patch not applied, server not running')
            return

        self._restoreStandardOutAndError()
        self._monkeyPatchLogger()

        self._applied = True

    def configure(self, address=DEFAULT_ADDRESS):
        # TODO: Complete documentation.

        if j.system.fs.exists(self.CONFIG_PATH):
            config = j.tools.inifile.open(self.CONFIG_PATH)
        else:
            config = j.tools.inifile.new(self.CONFIG_PATH)

        if not config.checkSection('main'):
            config.addSection('main')

        config.setParam('main', 'address', address)

    @property
    def isApplied(self):
        # TODO: Complete documentation.

        return self._applied

    def _log(self, message, level=5, tags='', dontprint=False, category=''):
        '''Logs a message by sending it to the message server.'''
        # TODO: Complete documentation.

        if j.logger.nolog or not isinstance(message, str):
            return

        if level <= j.logger.consoleloglevel and not dontprint\
                and j.application.interactive:
            print(message)

        if level <= j.logger.maxlevel:
            logMessage = ','.join([str(level), category, message])
            packedData = j.core.messagehandler.packMessage(
                j.enumerators.MessageServerMessageType.LOG.level, logMessage)

            self._messageServerClient.send(packedData)

    def _monkeyPatchLogger(self):
        '''Monkey patches the jshell logger.'''

        j.logger.cleanup = _doNothing
        j.logger.cleanupLogsOnFilesystem = _doNothing
        j.logger.clear = _doNothing
        j.logger.close = _doNothing
        j.logger.decodeLogMessage = _doNothing
        j.logger.exception = _doNothing
        j.logger.log = self._log
        j.logger.logs = []
        j.logger.logTargetAdd = _doNothing
        j.logger.logTargets = []
        j.logger.nolog = False

    def _restoreStandardOutAndError(self):
        '''Restores the standard out and standard error.'''

        if hasattr(sys, '_stdout_ori'):
            sys.stdout = sys._stdout_ori

        if hasattr(sys, '_stderr_ori'):
            sys.stderr = sys._stderr_ori
        else:
            sys.stderr = sys.stdout
