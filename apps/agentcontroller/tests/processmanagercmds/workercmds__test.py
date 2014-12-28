from JumpScale import j
import unittest
try:
    import ujson as json
except:
    import json
import time


descr = """
test worker CMDS of processmanager
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "processmanager.processmanagercmds.workercmds"
enable=True
priority=2

ROLE='node'

class TEST(unittest.TestCase):
    def setUp(self):
        import JumpScale.grid.agentcontroller
        import JumpScale.baselib.redis
        self.workercmds = j.clients.agentcontroller.getClientProxy('worker', '127.0.0.1')
        redisport=9999
        self.redis = j.clients.redis.getGeventRedisClient("127.0.0.1", redisport)

    def test_1_getQueuedJobs(self):
        qjobs = self.workercmds.getQueuedJobs(queue='test', _agentid=j.application.whoAmI.nid)
        original = len(qjobs)
        # job = {'gid': j.application.whoAmI.gid, 'id':111, 'queue':'test'}
        job = {'args': {}, 'category':  'jumpscript', 'cmd':  'jumpscale/loghandling', 'id': 111, 'jscriptid': 32, 'log': False, 'nid': 1, 'parent': None, 'queue':  'test', 'roles': [], 'state':  'SCHEDULED'}
        self.redis.rpush("queues:workers:work:test", json.dumps(job))
        self.redis.hset("workers:jobs", job['id'], json.dumps(job))

        qjobs = self.workercmds.getQueuedJobs(queue='test', _agentid=j.application.whoAmI.nid)

        self.assertEqual(len(qjobs), original + 1)


    def test_2_getJob(self):
        job = self.workercmds.getJob(jobid=111, _agentid=j.application.whoAmI.nid)

        self.assertEqual(job.get('id'), 111)

    def test_3_getFailedJobs(self): 
        qjobs = self.workercmds.getFailedJobs(queue='test', _agentid=j.application.whoAmI.nid)
        original = len(json.loads(qjobs))
        job = {'args': {}, 'category':  'jumpscript', 'cmd':  'jumpscale/loghandling', 'id': 112, 'jscriptid': 32, 'log': False, 'nid': 1, 'parent': None, 'queue':  'test', 'roles': [], 'state':  'ERROR'}
        self.redis.rpush("queues:workers:work:test", json.dumps(job))
        qjobs = self.workercmds.getFailedJobs(queue='test', _agentid=j.application.whoAmI.nid)

        self.assertEqual(len(json.loads(qjobs)), original + 1)

    # def test_4_resubmitJob(self):
    #     self.workercmds.resubmitJob(jobid=111, _agentid=j.application.whoAmI.nid)

    def test_5_removeJobs(self):
        self.workercmds.removeJobs(hoursago=0, _agentid=j.application.whoAmI.nid)
        qjobs = self.workercmds.getQueuedJobs(_agentid=j.application.whoAmI.nid)

        self.assertEqual(len(qjobs), 0)

