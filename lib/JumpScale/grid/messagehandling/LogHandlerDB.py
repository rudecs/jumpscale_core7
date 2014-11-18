import simplejson

from time import mktime, strptime
from JumpScale import j


class LogHandlerDB:

    MAX_FIND_RESULTS = 10000
    PERIOD_LENGTH = 3600
    FILEHANDLER_FLUSH_INTERVAL = 5
    ARAKOON_CATEGORIES_KEY = 'log.category.entries'

    def __init__(self, baseLogDir=None):
        self.baseLogDir = baseLogDir or j.system.fs.joinPaths(j.dirs.varDir,
                                                              'messagehandler', 'lj.db')

        self._fileHandlers = {}
        self.currentPeriod = 0

        try:
            gevent.spawn(self._flushFileHandlers)
        except:
            pass

        self._arakoonClient = None
        self._knownCategories = set()

    def _encode(self, data):
        if not data.endswith('\n'):
            data = '%s\n' % data

        return data

    def _decode(self, data):
        raise NotImplemented()

    def _flushFileHandlers(self):
        while True:
            for period, logFiles in self._fileHandlers.items():
                for logFile, logFileHandler in logFiles.items():
                    logFileHandler.flush()

            gevent.sleep(self.FILEHANDLER_FLUSH_INTERVAL)

    def getKnownCategories(self, sync=False):
        if sync:
            self.syncKnownCategories()

        return self._knownCategories

    def setArakoonClient(self, client):
        self._arakoonClient = client
        self.syncKnownCategories()

    def _addKnownCategory(self, category):
        self._knownCategories.add(category)

        if self._arakoonClient:
            self.syncKnownCategories()

    def syncKnownCategories(self):
        if self._arakoonClient.exists(self.ARAKOON_CATEGORIES_KEY):
            self._loadKnownCategories()

        self._storeKnownCategories()

    def _loadKnownCategories(self):
        categoriesString = self._arakoonClient.get(self.ARAKOON_CATEGORIES_KEY)
        categoryList = simplejson.loads(categoriesString)
        categorySet = set(categoryList)

        self._knownCategories.update(categorySet)

    def _storeKnownCategories(self):
        categoryList = list(self._knownCategories)
        categoriesString = simplejson.dumps(categoryList)

        self._arakoonClient.set(self.ARAKOON_CATEGORIES_KEY, categoriesString)

    def save(self, logmessage):
        messages = j.core.messagehandler.unPackMessageSeries(logmessage)

        for _, _, epoch, gid, nid, pid, data in messages:

            if epoch == 0:
                epoch = j.core.messagehandler.epoch
            category = data.split(',')[1]

            if category not in self._knownCategories:
                self._addKnownCategory(category)

            # Extract the hour from the epoch time.
            # Example: 1336378591 (08:16) => 1336377600 (08:00)
            period = int(round(epoch / self.PERIOD_LENGTH)) * self.PERIOD_LENGTH

            if period != self.currentPeriod:
                if self.currentPeriod in self._fileHandlers:
                    for fileHandler in self._fileHandlers[self.currentPeriod]:
                        fileHandler.close()

                    del(self._fileHandlers[self.currentPeriod])

                self._fileHandlers[period] = {}
                self.currentPeriod = period

            logDir = self.pm_getLogDir(gid, nid, pid)

            if not j.system.fs.exists(logDir):
                j.system.fs.createDir(logDir)

            logFile = j.system.fs.joinPaths(logDir, str(period) + '.lj.db')

            if logFile not in self._fileHandlers[period]:
                self._fileHandlers[period][logFile] = open(logFile, 'ab')

            data = ','.join([str(gid), str(nid), str(pid), str(epoch), data])
            logEntry = self._encode(data)

            self._fileHandlers[period][logFile].write(logEntry)

    def _findLogDirsByIds(self, gid=None, nid=None, pid=None):
        filteredLogDirs = set()

        if gid != None and pid != None and nid != None:
            logDir = self.pm_getLogDir(gid, nid, pid)

            if j.system.fs.exists(logDir):
                filteredLogDirs.add(logDir)
        elif gid == None and pid == None and nid == None:
            return j.system.fs.listDirsInDir(self.baseLogDir)
        else:
            logDirs = j.system.fs.listDirsInDir(self.baseLogDir)

            for logDir in logDirs:
                logDirName = j.system.fs.getBaseName(logDir)
                gid2, nid2, pid2 = self._extractIdsFromLogDirName(logDirName)

                if (gid == None or gid == gid2) \
                    and (nid == None or nid == nid2) \
                        and (pid == None or pid == pid2):
                    filteredLogDirs.add(logDir)

        return filteredLogDirs

    def _findLogDirsByIdCombinations(self, idCombinations):
        logDirs = set()

        for idCombination in idCombinations:
            gid = idCombination[0]
            nid = idCombination[1]
            pid = idCombination[2]

            dirs = self._findLogDirsByIds(gid, nid, pid)
            logDirs.update(dirs)

        return logDirs

    def _filterLogFilePathsByTime(self, logDirs, fromEpoch=None, toEpoch=None):
        filteredLogFilePaths = set()

        for logDir in logDirs:
            logFilePaths = j.system.fs.listFilesInDir(logDir)

            for logFilePath in logFilePaths:
                logFileName = j.system.fs.getBaseName(logFilePath)
                period = int(logFileName.split('.')[0])
                periodInTimeWindow = self._periodInTimeWindow(period, fromEpoch,
                                                              toEpoch)

                if periodInTimeWindow:
                    filteredLogFilePaths.add(logFilePath)

        return filteredLogFilePaths

    def _timeInTimeWindow(self, epoch, fromEpoch=None, toEpoch=None):
        return (fromEpoch == None or epoch >= fromEpoch) \
            and (toEpoch == None or epoch <= toEpoch)

    def _periodInTimeWindow(self, period, fromEpoch=None, toEpoch=None):
        # Note that the period is incremented with the length of the period.
        return (fromEpoch == None or (period + self.PERIOD_LENGTH) >= fromEpoch) \
            and (toEpoch == None or period <= toEpoch)

    def find(self, gid=None, nid=None, pid=None, fromDateTime=None, toDateTime=None, categories=None, levels=None):
        logDirs = self._findLogDirsByIds(gid, nid, pid)

        return self._findInLogDirs(logDirs, fromDateTime, toDateTime,
                                   categories, levels)

    def findByIdCombinations(self, idCombinations=None, fromDateTime=None, toDateTime=None, categories=None, levels=None):
        idCombinations = idCombinations or list()

        logDirs = self._findLogDirsByIdCombinations(idCombinations)

        return self._findInLogDirs(logDirs, fromDateTime, toDateTime,
                                   categories, levels)

    def _findInLogDirs(self, logDirs, fromDateTime=None, toDateTime=None, categories=None, levels=None):
        fromEpoch = self._transformDateTimeToEpoch(fromDateTime)
        toEpoch = self._transformDateTimeToEpoch(toDateTime)

        logFiles = self._filterLogFilePathsByTime(logDirs, fromEpoch, toEpoch)

        logEntries = set()

        for logFile in logFiles:
            f = open(logFile)
            logEntry = f.readline()

            while logEntry and len(logEntries) < self.MAX_FIND_RESULTS:
                try:
                    time, level, category, message = \
                        self._decodeLogEntry(logEntry)
                    logEntryIsValid = True
                except RuntimeError:
                    logEntryIsValid = False
                    j.logger.log('Couln\'t decode log entry "%s"' % logEntry)

                if logEntryIsValid:
                    timeOk = self._timeInTimeWindow(time, fromEpoch, toEpoch)
                    levelOk = not levels or level in levels
                    categoryOk = not categories or category in categories

                    if timeOk and levelOk and categoryOk:
                        logEntries.add(logEntry)

                logEntry = f.readline()

        return logEntries

    def _transformDateTimeToEpoch(self, dateTime):
        if isinstance(dateTime, int):
            epoch = float(dateTime)
        elif isinstance(dateTime, str):
            pattern = '%d/%m/%Y %H:%M:%S'
            structTime = strptime(dateTime, pattern)
            epoch = float(mktime(structTime))
        elif dateTime == None:
            epoch = None

        return epoch

    def pm_getLogDirName(self, gid, nid, pid):
        return '%s_%s_%s' % (gid, nid, pid)

    def pm_getLogDir(self, gid, nid, pid):
        logDirName = self.pm_getLogDirName(gid, nid, pid)
        return j.system.fs.joinPaths(self.baseLogDir, logDirName)

    def _encodeLogEntry(self, epoch, level, category, message):
        return [epoch, level, category, message].join(',')

    def _decodeLogEntry(self, entry):
        data = entry.split(',')

        if len(data) < 6:
            raise RuntimeError('Couldn\'t decode log entry %s' % entry)

        epoch = int(data[3])
        level = int(data[4])
        category = str(data[5])
        message = ','.join(data[6:])

        return epoch, level, category, message

    def _extractIdsFromLogDirName(self, dirName):
        ids = dirName.split('_')

        if len(ids) != 3:
            raise RuntimeError('Couldn\'t extract ids from dir name %s'
                               % dirName)

        gid = int(ids[0])
        nid = int(ids[1])
        pid = int(ids[2])

        return gid, nid, pid
