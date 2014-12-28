import unittest
from JumpScale import j


enable = True
author = "Jo De Boeck <deboeckj@codescalers.com"
descr = "Test agentcontroller proxy feature"
organization = "JumpScale"
version = "1.0"
category = ""
license = "BSD"
priority = 1

class TEST(unittest.TestCase):
    def setUp(self):
        import JumpScale.grid.agentcontroller
        self.cl = j.clients.agentcontroller.getClientProxy(category='tests')
        self.msg = 'a test message'

    def test_echo(self):
        result = self.cl.echoTest(self.msg, _agentid=j.application.whoAmI.nid)
        self.assertEqual(self.msg, result)

    def test_raise(self):
        with self.assertRaises(Exception):
            self.cl.raiseTest(self.msg, _agentid=j.application.whoAmI.nid)
