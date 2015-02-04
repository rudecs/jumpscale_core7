from JumpScale import j
import unittest
import time


descr = """
test basic functioning of agentcontroller
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "agentcontroller.basic"
enable=True
priority=2

ROLE = 'node'

class TEST(unittest.TestCase):

    def setUp(self):
        import JumpScale.grid.agentcontroller
        self.client=j.clients.agentcontroller.get()
        self.osisclient = j.clients.osis.getByInstance('main')
        self.nid = j.application.whoAmI.nid

    def test_basic_execution(self):
        kwargs = {'msg': 'test msg'}
        result1 = self.client.executeJumpscript('jumpscale', 'echo', self.nid, ROLE, args=kwargs, wait=True)
        self.assertEqual(result1['result'], kwargs['msg'])

    def test_log(self):
        kwargs = {'logmsg': 'test log msg'}
        job = self.client.executeJumpscript('jumpscale', 'log', self.nid, ROLE, args=kwargs, wait=True)
        self.assertIsInstance(job, dict)
        self.assertEqual(job['state'], 'OK')
        query = {"query":{"bool":{"must":[{"term":{"category":"test_category"}}]}}}
        import JumpScale.grid.osis
        osis_logs = j.clients.osis.getCategory(self.osisclient, "system", "log")

        start = time.time()
        while start + 5 > time.time():
            result = osis_logs.search(query)['hits']['hits']
            if result:
                break
        self.assertGreater(result, 0)

    def test_error(self):
        self.client.execute('jumpscale', 'error', ROLE, dieOnFailure=False)
        query = {"query":{"bool":{"must":[{"term":{"state":"error"}}, {"term":{"cmd":"error"}}]}}}
        osis_jobs = j.clients.osis.getCategory(self.osisclient, "system", "job")
        start = time.time()
        while start + 5 > time.time():
            result = osis_jobs.search(query)['result']
            if result:
                break

        self.assertGreater(len(result), 0)

