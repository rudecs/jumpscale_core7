import unittest
import re
import time
from JumpScale import j
try:
    import ujson as json
except:
    import json
import random

descr = """
performance test
"""

organization = "jumpscale"
author = "incubaid"
license = "bsd"
version = "1.0"
category = "osis.basic.testset"
enable=False
priority=50

import JumpScale.grid.osis


class TEST():
    def randomMAC(self):
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(["%02x" % x for x in mac])

    def setUp(self):
        self.client = j.core.osis.getClient()
        self.nodeclient =j.core.osis.getClientForCategory(self.client, 'system', 'fake4test')
        self.prefix = time.time()

    def test_set(self):
        # We first set some elements and verify the reponse
        obj = self.nodeclient.new()
        obj.name = "%s_1" % self.prefix
        obj.netaddr = {self.randomMAC(): ['127.0.0.1', '127.0.0.2']}
        obj.machineguid = j.tools.hash.md5_string(str(list(obj.netaddr.keys())))
        key, new, changed = self.nodeclient.set(obj)
        testresult = self.verify_id(key) and new and changed
        assert testresult==True

    def test_set_and_get(self):
        # Set a object and get it back, check the content.
        obj = self.nodeclient.new()
        obj.name = "%s_1" % self.prefix
        obj.netaddr = {self.randomMAC(): ['127.0.0.1', '127.0.0.2']}
        obj.machineguid = j.tools.hash.md5_string(str(list(obj.netaddr.keys())))
        key, new, changed = self.nodeclient.set(obj)
        obj = json.loads(self.client.get("system", "fake4test", key))
        assert obj['name']== "%s_1" % self.prefix

    def test_set_and_self(self):
        numbers = list(range(10))
        items = self.client.list("system", "fake4test")
        startnr = len(items)
        for i in numbers:
            obj = self.nodeclient.new()
            obj.name = "%s_%s" % (self.prefix, i)
            obj.netaddr = {self.randomMAC(): ['127.0.0.1', '127.0.0.2']}
            obj.machineguid = j.tools.hash.md5_string(str(list(obj.netaddr.keys())))
            key, new, changed = self.nodeclient.set(obj)
        items = self.client.list("system", "fake4test")
        assert len(items)== startnr + 10

    def test_set_and_delete(self):
        obj = self.nodeclient.new()
        obj.name = "%s_1" % self.prefix
        obj.netaddr = {self.randomMAC(): ['127.0.0.1', '127.0.0.2']}
        obj.machineguid = j.tools.hash.md5_string(str(list(obj.netaddr.keys())))
        key, new, changed = self.nodeclient.set(obj)
        obj = self.client.get("system", "fake4test", key)
        self.client.delete("system", "fake4test", key)
        items = self.client.list("system", "fake4test")
        if key in items:
            deleted = False
        else:
            deleted = True
        assert deleted==True

    def test_find(self):
        pass

    def verify_id(self, id):
        """
        This function verifies a id, e.g checks if its in the correct format
        Id should be clusterid_objectid
        Clusterid and objectid are both integers
        """
        regex = '^\d+[_]\d+$'
        if re.search(regex, id):
            return True
        else:
            return False

    def tearDown(self):
        self.client.deleteNamespaceCategory("system","fake4test")
