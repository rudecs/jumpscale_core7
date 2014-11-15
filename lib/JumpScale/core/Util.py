

import sys
import os
import time
import re

if sys.platform.startswith('linux') or sys.platform.startswith('sunos'):
    import fcntl

from JumpScale import j

# THIS METHOD IS NOT THREADSAFE

#TODO Fixup singleton-like behaviour
class Util:

    _LOCKPATHLINUX = "/tmp/run"
    __LOCKDICTIONARY = {}

    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self._LOCKPATHWIN = os.getcwd()+os.sep+'tmp'+os.sep+'run'+os.sep

    def cleanupString(self, string, replacewith="_", regex="([^A-Za-z0-9])"):
        # Please don't use the logging system here. The logging system
        # needs this method, using the logging system here would
        # introduce a circular dependency. Be careful not to call other
        # functions that use the logging system.

        """ remove all non numeric or alphanumeric characters """
        return re.sub(regex, replacewith, string)

    def lock(self, lockname, locktimeout=60):
        """ Take a system-wide interprocess exclusive lock. Default timeout is 60 seconds """

        if locktimeout < 0:
            raise RuntimeError("Cannot take lock [%s] with negative timeout [%d]" % (lockname, locktimeout))

        if j.system.platformtype.isUnix():
            # linux implementation
            lockfile = self._LOCKPATHLINUX + os.sep + self.cleanupString(lockname)
            j.system.fs.createDir(Util._LOCKPATHLINUX)
            j.system.fs.createEmptyFile(lockfile)

            # Do the locking
            lockAcquired = False
            for i in range(locktimeout+1):
                try:
                    myfile = open(lockfile, "r+")
                    fcntl.flock(myfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    lockAcquired = True
                    self.__LOCKDICTIONARY[lockname] = myfile
                    break
                except IOError:
                    # Did not get the lock :( Sleep 1 second and then retry
                    time.sleep(1)
            if not lockAcquired:
                myfile.close()
                raise RuntimeError("Cannot acquire lock [%s]" % (lockname))

        elif j.system.platformtype.isWindows():
            raise NotImplementedError

    def unlock(self, lockname):
        """ Unlock system-wide interprocess lock """
        if j.system.platformtype.isUnix():
            try:
                myfile = self.__LOCKDICTIONARY.pop(lockname)
                fcntl.flock(myfile.fileno(), fcntl.LOCK_UN)
                myfile.close()
            except Exception, exc:
                raise RuntimeError("Cannot unlock [%s] with ERROR:%s" % (lockname, str(exc)))

        elif j.system.platformtype.isWindows():
            raise NotImplementedError