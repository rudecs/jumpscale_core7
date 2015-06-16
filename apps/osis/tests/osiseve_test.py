import unittest
from JumpScale import j
from JumpScale.grid.osis.OsisEveClient import NotFound

class OsisEveTest(object):
    NAME = None
    def setUp(self):
        self.cl = j.clients.osis.getEveClient('http://localhost:5545')
        self.tcl = getattr(self.cl, self.NAME)

    def test_new(self):
        self.assertIsNotNone(self.tcl.user.new())

    def test_set(self, name='My Name'):
        user = self.tcl.user.new()
        user.guid = j.base.idgenerator.generateGUID()
        user.id = name
        user.data = 'some random data'
        user.domain = 'mydomain'
        response = self.tcl.user.set(user)
        self.assertIsInstance(response, dict)
        self.assertEqual(response['_status'], 'OK', msg=response)
        return user

    def test_notfound(self):
        self.assertRaises(NotFound, self.tcl.user.get, 'somerandomid')

    def test_get(self):
        user = self.test_set()
        user2 = self.tcl.user.get(user.guid)
        self.assertEqual(user.guid, user2.guid)

    def test_update(self):
        user = self.test_set()
        user.domain = 'adomain'
        self.tcl.user.update(user)
        newuser = self.tcl.user.get(user.guid)
        self.assertEqual(newuser.domain, 'adomain')

    def test_exists(self):
        user = self.test_set()
        self.assertTrue(self.tcl.user.exists(user.guid))
        self.assertFalse(self.tcl.user.exists('ranomdid'))

    def test_search(self):
        randomname = j.base.idgenerator.generateGUID()
        self.test_set(name=randomname)
        results = self.tcl.user.search({'id': randomname})
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)

    def test_list(self):
        self.test_set()
        results = self.tcl.user.list()
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)

class OsisEveMongoTest(OsisEveTest, unittest.TestCase):
    NAME = 'system'

class OsisEveSqlTest(OsisEveTest, unittest.TestCase):
    NAME = 'sqlnamespace'
