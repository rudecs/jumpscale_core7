import unittest
from JumpScale import j
import time


enable = True
author = "Jo De Boeck <deboeckj@codescalers.com"
descr = "Test what happens when service are not running or restart"
organization = "JumpScale"
version = "1.0"
category = ""
license = "BSD"
priority = 1

class TEST(unittest.TestCase):
    def setUp(self):
        import JumpScale.grid.agentcontroller
        self.client = j.clients.agentcontroller.get()
        self.args = {'msg': 'a test message'}


    #@unittest.skip('does not work TODO')
    def test_processmanager_restart(self):
        result = self.client.execute('jumpscale', 'echo', nid=j.application.whoAmI.nid, wait=True, **self.args)
        self.assertEqual(result, self.args['msg'])
        j.system.platform.ubuntu.stopService('processmanager')
        j.system.platform.ubuntu.startService('processmanager')
        time.sleep(2)

        job = self.client.scheduleCmd(j.application.whoAmI.gid,j.application.whoAmI.nid, 'jumpscale', 'echo', args=self.args, queue="io", log=True, timeout=60, wait=True)
        result = self.client.waitJumpscript(job=job)
        self.assertEqual(result['result'], self.args['msg'])

    def test_agentcontroller_restart(self):
        result = self.client.execute('jumpscale', 'echo', nid=j.application.whoAmI.nid, wait=True, **self.args)
        self.assertEqual(result, self.args['msg'])
        j.tools.startupmanager.restartProcess('jumpscale', 'agentcontroller')
        result = self.client.execute('jumpscale', 'echo', nid=j.application.whoAmI.nid, wait=True, **self.args)
        self.assertEqual(result, self.args['msg'])

