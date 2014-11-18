import errno
import signal
import time

from JumpScale import j
from .utils import printInDebugMode
from .server import MessageServer


class MessageServerConfig(object):

    def __init__(self, name, address=None, forwardAddresses=None, storeLocally=True):
        self._name = name
        address = address or '127.0.0.1:7777'
        self._address = self._completeAddress(address)
        self._forwardAddresses = set()

        if forwardAddresses:
            for address in forwardAddresses:
                completedAddress = self._completeAddress(address)
                self._forwardAddresses.add(completedAddress)

        self._storeLocally = storeLocally

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @property
    def forwardAddresses(self):
        return tuple(self._forwardAddresses)

    @property
    def storeLocally(self):
        return self._storeLocally

    def _completeAddress(self, address):
        ip, _, port = address.partition(':')

        ip = ip or '127.0.0.1'
        port = port or '7777'

        return '%s:%s' % (ip, port)


class MessageServerManager(object):

    _SCRIPT_PROCESS_NAME = 'python'
    _SCRIPT_FILE_NAME = 'server.py'
    _START_TIMEOUT = _STOP_TIMEOUT = 5  # Measurement in seconds.

    def __init__(self, name, address=None, forwardAddresses=None, store=True, echo=False):
        self._name = name
        self._address = address
        self.forwardAddresses = forwardAddresses
        self.storeLocal = store
        self.echo = False

        pidFileName = 'message_server_%s.pid' % self._name
        self._pidFile = j.system.fs.joinPaths(j.dirs.pidDir, pidFileName)

    @classmethod
    def createFromConfig(cls, config):
        return MessageServerManager(config.name, config.address,
                                    config.forwardAddresses, config.storeLocally)

    def getStartCommand(cls):
        return self._createStartCommand()

    def start(self, force=False, inprocess=False):

        if inprocess:
            server = MessageServer(self._address, self.storeLocal, self._pidFile, self.echo)

            for address in self.forwardAddresses:
                client = MessageServerClient(address)
                server.forwardClients.add(client)

            server.start()
            return

        if self.isRunning and not force:
            printInDebugMode('Cannot start message server, already running')
            return

        command = self._createStartCommand()

        printInDebugMode('Starting message server with command: %s' % command)

        j.system.process.runDaemon(command)

        remainingSeconds = self._START_TIMEOUT
        time.sleep(5)
        while not self.isRunning:
            printInDebugMode('Waiting %d more seconds for message server to be'
                             ' started' % remainingSeconds)

            time.sleep(1)
            remainingSeconds -= 1

            if not remainingSeconds:
                raise RuntimeError('Failed to start message server')

        printInDebugMode('Started message server')

    def stop(self, force=False):
        if not self.isRunning and not force:
            printInDebugMode('Cannot stop message server, not running')
            return

        pid = self._getPidFromPidFile()

        if force:
            stopSignal = signal.SIGKILL
        else:
            stopSignal = signal.SIGTERM

        printInDebugMode('Stopping message server')

        j.system.process.kill(pid, sig=stopSignal)

        remainingSeconds = self._STOP_TIMEOUT

        while self.isRunning:
            printInDebugMode('Waiting %d more seconds for message server to be'
                             ' stopped' % remainingSeconds)

            time.sleep(1)
            remainingSeconds -= 1

            if not remainingSeconds:
                raise RuntimeError('Failed to stop message server')

        j.system.fs.remove(self._pidFile)

        printInDebugMode('Stopped message server')

    def restart(self, force=False):
        self.stop()
        self.start(force=force)

    @property
    def isRunning(self):
        #@TODO this needs to be fixed, a real test needs to be done, if e.g. server crashes this can still return positive
        try:
            pid = self._getPidFromPidFile()
        except (IOError, ValueError) as error:
            j.logger.exception('Can\'t get pid from pid file (error: %s)'
                               % error)
            return False

        status = j.system.process.checkProcessForPid(pid,
                                                     self._SCRIPT_PROCESS_NAME)

        # status == 0 => server running
        # status == 1 => server not running
        return status == 0

    @property
    def pid(self):
        if j.system.fs.exists(self._pidFile):
            return self._getPidFromPidFile()
        else:
            return None

    def _createStartCommand(self):
        moduleFile = j.system.fs.getParent(__file__)
        serverFile = j.system.fs.joinPaths(moduleFile, self._SCRIPT_FILE_NAME)
        pieces = [self._SCRIPT_PROCESS_NAME, serverFile]

        pieces.append('-a %s' % self._address)

        if self.forwardAddresses:
            addresses = ' '.join(self.forwardAddresses)
            pieces.append('-f %s' % addresses)

        pieces.append('-p %s' % self._pidFile)

        if self._store:
            pieces.append('-s')

        return ' '.join(pieces)

    def _getPidFromPidFile(self, safe=False):
        try:
            pidStr = j.system.fs.fileGetContents(self._pidFile)
        except IOError as error:
            if error.errno == errno.ENOENT:
                raise IOError('Could\'t get message server pid, pid file'
                              ' doesn\'t exists')
            else:
                raise IOError('Could\'t get message server pid (error: %s)'
                              % error)

        try:
            pid = int(pidStr.strip())
        except ValueError as error:
            message = 'Could\'t get message server pid, invalid pid file' \
                ' contents (error: %s)' % error
            j.logger.log(message)
            raise ValueError(message)

        return pid


class MessageServerManagerFactory(object):

    _CONFIG_EXTENSION = 'cfg'
    _CONFIG_BASE_DIR = j.system.fs.joinPaths(j.dirs.cfgDir, 'messageserver')

    def create(self, name, address=None, forwardAddresses=None,
               storeLocally=False):
        '''
        Creates a new configuration and creates a new  message server manager
        instance from it.

        @param name: name of the server
        @type name: str

        @param address: address the server should use
        @type address: str

        @param forwardAddresses: addresses the server should forward to
        @type forwardAddresses: set()

        @param storeLocally: flag indicating if the server should store its messages locally or not
        @type storeLocally: bool

        @return: message server manager
        @rtype: MessageServerManager
        '''

        if name in self.list():
            raise RuntimeError('Couln\'t create server manager, name "%s"'
                               ' already in use' % name)

        config = MessageServerConfig(name, address, forwardAddresses,
                                     storeLocally)
        self._storeConfig(config)

        return MessageServerManager.createFromConfig(config)

    def delete(self, name):
        '''
        Deletes an message server manager by deleting its configuration.

        @param name: name of the server
        @type name: str
        '''

        if name not in self.list():
            raise RuntimeError('Couln\'t delete server manager, no'
                               ' configuration found for name %s' % name)

        config = self._loadConfig(name)
        server = MessageServerManager.createFromConfig(config)

        if server.isRunning:
            raise RuntimeError('Couln\'t delete management object, server'
                               ' still running')

        self._deleteConfig(name)

    def get(self, name):
        '''
        Loads a configuration and creates an message server manager instance
        from it.

        @param name: name of the server
        @type name: str

        @return: message server manager
        @rtype: MessageServerManager
        '''

        if name not in self.list():
            raise RuntimeError('Couln\'t get server manager, no configuration'
                               ' found for name %s' % name)

        config = self._loadConfig(name)

        return MessageServerManager.createFromConfig(config)

    def list(self):
        '''
        List all message server managers their names.

        @return: set containing all message server managers their names
        @rtype: set()
        '''

        if not j.system.fs.exists(self._CONFIG_BASE_DIR):
            return set()

        configFilter = '*.%s' % self._CONFIG_EXTENSION
        configFiles = j.system.fs.listFilesInDir(self._CONFIG_BASE_DIR,
                                                 filter=configFilter)

        names = set()
        extensionLength = len(self._CONFIG_EXTENSION) + 1

        for configFile in configFiles:
            fileName = j.system.fs.getBaseName(configFile)
            fileName = fileName[:-extensionLength]
            names.add(fileName)

        return names

    def _deleteConfig(self, name):
        configPath = self._getConfigPath(name)
        j.system.fs.remove(configPath)

    def _loadConfig(self, name):
        iniConfigPath = self._getConfigPath(name)
        iniConfig = j.tools.inifile.open(iniConfigPath)

        address = iniConfig.getValue('main', 'address')

        forwardAddressesStr = iniConfig.getValue('main', 'forwardaddresses')

        if forwardAddressesStr:
            forwardAddresses = forwardAddressesStr.split(',')
        else:
            forwardAddresses = []

        storeLocallyStr = iniConfig.getValue('main', 'storelocally')
        storeLocally = storeLocallyStr.lower() == 'true'

        return MessageServerConfig(name, address, forwardAddresses,
                                   storeLocally)

    def _getConfigPath(self, name):
        fileName = '%s.%s' % (name, self._CONFIG_EXTENSION)
        return j.system.fs.joinPaths(self._CONFIG_BASE_DIR, fileName)

    def _storeConfig(self, config):
        iniConfigPath = self._getConfigPath(config.name)
        iniConfig = j.tools.inifile.new(iniConfigPath)

        iniConfig.addSection('main')
        iniConfig.setParam('main', 'address', config.address)

        forwardAddressesStr = ', '.join(config.forwardAddresses)
        iniConfig.setParam('main', 'forwardaddresses', forwardAddressesStr)

        storeLocallyStr = str(config.storeLocally).lower()
        iniConfig.setParam('main', 'storelocally', storeLocallyStr)
