from JumpScale import j
import unittest


descr = """
test basic functioning of agentcontroller new way
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "agentcontroller.basic.new"
enable=True
priority=2

ROLE='node'

class TEST(unittest.TestCase):
    def setUp(self):
        import JumpScale.grid.agentcontroller
        self.client=j.clients.agentcontroller.get("127.0.0.1")
        self.args = {'msg': 'test msg'}

    def test_schedule(self):
        cmdcategory="jumpscale"
        cmdname="echo"

        job = self.client.scheduleCmd(j.application.whoAmI.gid,j.application.whoAmI.nid, cmdcategory, cmdname, args=self.args, queue="default", log=True, timeout=60, wait=True)
        self.assertEqual(job['state'], 'SCHEDULED')
        job = self.client.waitJumpscript(job=job)
        self.assertIsInstance(job, dict)
        self.assertEqual(job['result'], self.args['msg'])


    def test_execute_withrole(self): 
        result1 = self.client.execute('jumpscale', 'echo', role=ROLE, wait=True, **self.args)
        self.assertEqual(result1, self.args['msg'])

