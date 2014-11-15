from contextlib import contextmanager
import unittest

from arakoon_store import ArakoonKeyValueStore
from file_system_store import FileSystemKeyValueStore
from memory_store import MemoryKeyValueStore
from JumpScale import j
from store import KeyValueStoreType

if not q._init_called:
    from JumpScale.core.InitBase import q

class PatchedTimeContext(object):
    def __init__(self, time):
        self.time = time

@contextmanager
def pathed_time(t):
    ctx = PatchedTimeContext(time=t)

    def fakeGetTimeEpoch():
        return ctx.time

    origGetTimeEpoch = j.base.time.getTimeEpoch
    j.base.time.getTimeEpoch = fakeGetTimeEpoch
    # Make sure we restore the original getTimeEpoch function
    try:
        yield ctx
    finally:
        j.base.time.getTimeEpoch = origGetTimeEpoch

class KeyValueStoreTestCaseBase(object):

    STORE_NAME = 'test_store'
    STORE_NAMESPACE = 'test_namespace'
    STORE_CATEGORY = 'test_category'
    STORE_KEY = 'test_key'
    STORE_VALUE = 'test_value'

    def setUp(self):
        raise NotImplementedError()

    def testFactory(self):
        raise NotImplementedError()

    def testGetSetDeleteAndExists(self):
        with self.assertRaises(KeyError):
            self._store.get(self.STORE_CATEGORY, self.STORE_KEY)

        exists = self._store.exists(self.STORE_CATEGORY, self.STORE_KEY)
        self.assertEquals(exists, False)

        self._store.set(self.STORE_CATEGORY, self.STORE_KEY, self.STORE_VALUE)

        exists = self._store.exists(self.STORE_CATEGORY, self.STORE_KEY)
        self.assertEquals(exists, True)

        value = self._store.get(self.STORE_CATEGORY, self.STORE_KEY)
        self.assertEquals(value, self.STORE_VALUE)

        self._store.delete(self.STORE_CATEGORY, self.STORE_KEY)

        exists = self._store.exists(self.STORE_CATEGORY, self.STORE_KEY)
        self.assertEquals(exists, False)

    def testListEmptyPrefix(self):
        self._store.set(self.STORE_CATEGORY, self.STORE_KEY, self.STORE_VALUE)
        actual = self._store.list(self.STORE_CATEGORY, "")
        expected = [self.STORE_KEY]
        self.assertEqual(expected, actual)

    def testListUnknownPrefix(self):
        self._store.set(self.STORE_CATEGORY, self.STORE_KEY, self.STORE_VALUE)
        actual = self._store.list(self.STORE_CATEGORY, "bad")
        expected = []
        self.assertEqual(expected, actual)

    def testListFullPrefix(self):
        self._store.set(self.STORE_CATEGORY, self.STORE_KEY, self.STORE_VALUE)
        actual = self._store.list(self.STORE_CATEGORY, self.STORE_KEY)
        expected = [self.STORE_KEY]
        self.assertEqual(expected, actual)

    def testIncrement(self):
        name = "testing-1-2-3"
        i = self._store.increment(name)
        self.assertEqual(1, i)
        for e in xrange(2, 10):
            i = self._store.increment(name)
            self.assertEqual(e, i)

    def testLock(self):
        lType = "test-lock"
        info = "Just testing the lock code"
        namespace = "lock"

        with pathed_time(1334250385) as pt:
            self._store.lock(lType, info, timeout=2, timeoutwait=0)

            pt.time += 1
            parts = self._store.lockCheck(lType)
            self.assertEqual(len(parts), 4, "Expected 4 return values from lockCheck")
            result, setterId, time, info = parts
            self.assert_(result, "Expected the lock to be set, but it wasn't")

            pt.time += 2
            parts = self._store.lockCheck(lType)
            self.assertEqual(len(parts), 4, "Expected 4 return values from lockCheck")
            result, setterId, time, info = parts
            self.assert_(not result, "Expected the lock to be released, but it wasn't")

        # Check if the lock was cleaned up
        with self.assertRaises(KeyError):
            self._store.get(namespace, lType)

    def testLockTwice(self):
        lType = "test-lock"
        info = "Just testing the lock code"
        info2 = "Attempting to take the lock a second time"
        timeout = 2

        before = j.base.time.getTimeEpoch()
        self._store.lock(lType, info, timeout=timeout, timeoutwait=0)
        self._store.lock(lType, info2, timeout=3, timeoutwait=10)
        after = j.base.time.getTimeEpoch()
        difference = after - before
        self.assert_(difference > (timeout - 1), "It seems like the original "
                "lock was not held long enough")

    def testListCategories(self):
        cat1 = "category 1"
        cat2 = "category 2"
        self._store.set(cat1, "key1", "foo")
        self._store.set(cat2, "key2", "bar")
        actual = self._store.listCategories()
        expected = [cat1, cat2]
        self.assertEqual(set(expected), set(actual))


class ArakoonKeyValueStoreTestCase(unittest.TestCase,
    KeyValueStoreTestCaseBase):

    STORE_CLUSTER = 'test_cluster_name_1337'

    def setUp(self):
        '''
        Cleans up and sets up a an Arakoon cluster.
        '''

        self.cleanUp()

        cluster = j.manage.arakoon.getCluster(self.STORE_CLUSTER)
        # Avoid conflicts with other cluster ports
        cluster.setUp(1, basePort=54321)
        cluster.start()

        config = j.clients.arakoon.getClientConfig(self.STORE_CLUSTER)
        config.generateFromServerConfig()

        self._store = ArakoonKeyValueStore(self.STORE_CLUSTER,
            self.STORE_NAMESPACE)

    def tearDown(self):
        self.cleanUp()

    def cleanUp(self):
        '''
        Tears down the Arakoon test cluster and client and removes the
        directories related to them.
        '''

        cluster = j.manage.arakoon.getCluster(self.STORE_CLUSTER)
        cluster.stop()
        cluster.tearDown()
        cluster.remove()

        dbDir = j.system.fs.joinPaths(j.dirs.varDir, 'db', self.STORE_CLUSTER)
        j.system.fs.removeDirTree(dbDir)

        logDir = j.system.fs.joinPaths(j.dirs.logDir, self.STORE_CLUSTER)
        j.system.fs.removeDirTree(logDir)

    def testFactory(self):
        storeA = j.db.keyvaluestore.getStore(KeyValueStoreType.ARAKOON,
            self.STORE_CLUSTER, self.STORE_NAMESPACE)

        storeB = j.db.keyvaluestore.getArakoonStore(self.STORE_CLUSTER,
            self.STORE_NAMESPACE)

        self.assertEquals(storeA, storeB)


class FileSystemKeyValueStoreTestCase(unittest.TestCase,
    KeyValueStoreTestCaseBase):

    def setUp(self):
        self._storeBaseDir = j.system.fs.joinPaths(j.dirs.tmpDir)

        self.cleanUp()

        self._store = FileSystemKeyValueStore(self.STORE_NAME,
            self.STORE_NAMESPACE,  self._storeBaseDir)

    def tearDown(self):
        self.cleanUp()

    def cleanUp(self):
        self._storeDir = j.system.fs.joinPaths(j.dirs.tmpDir, self.STORE_NAME,
            self.STORE_NAMESPACE)
        j.system.fs.removeDirTree(self._storeDir)

    def testFactory(self):
        storeA = j.db.keyvaluestore.getStore(KeyValueStoreType.FILE_SYSTEM,
            self.STORE_NAME, self.STORE_NAMESPACE)

        storeB = j.db.keyvaluestore.getFileSystemStore(self.STORE_NAME,
            self.STORE_NAMESPACE)

        self.assertEquals(storeA, storeB)

class MemoryKeyValueStoreTestCase(unittest.TestCase, KeyValueStoreTestCaseBase):

    def setUp(self):
        self._store = MemoryKeyValueStore()

    def testFactory(self):
        storeA = j.db.keyvaluestore.getStore(KeyValueStoreType.MEMORY,
            self.STORE_NAME, self.STORE_NAMESPACE)

        storeB = j.db.keyvaluestore.getMemoryStore(self.STORE_NAME,
            self.STORE_NAMESPACE)

        self.assertEquals(storeA, storeB)
