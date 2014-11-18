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
basic functioning of osis (test set)
"""

organization = "jumpscale"
author = "incubaid"
license = "bsd"
version = "1.0"
category = "osis.basic.testset"
enable=True
priority=1
send2osis=False

import JumpScale.grid.osis


class TEST(unittest.TestCase):

    def randomMAC(self):
        return j.base.idgenerator.generateGUID().replace("-","")

    def setUp(self):
        self.client = j.core.osis.getClientByInstance('main')
        self.osisclient =j.core.osis.getClientForCategory(self.client, 'system', 'fake4test')
        self.prefix = time.time()
        

    def test_setGetBasicVerify(self):
        # We first set some elements and verify the reponse
        obj = self.osisclient.new()
        obj.name = "test"
        obj.netaddr = {"AABBCCDDEEFFGG": ['127.0.0.1', '127.0.0.2']}

        ckeyOriginal=obj.getContentKey()

        assert ckeyOriginal=='f7d877013a2d6c853092e55bad32435b'
        assert obj.getUniqueKey()=='098f6bcd4621d373cade4e832627b4f6'

        key,new,changed=self.osisclient.set(obj)
        key2,new,changed=self.osisclient.set(obj)

        print("2x save should have same key")
        assert key==key2

        print("check 2nd save new & changed are not new or changed")
        assert new==False
        assert changed==False

        print("test content key does not get modified when set")
        assert ckeyOriginal==obj.getContentKey()

        print("retrieve obj from db")
        obj2=self.osisclient.get(key)
        print("test content key needs to remain same after fetching object")

        assert ckeyOriginal==obj2.getContentKey()

        obj.description="a descr"
        print("obj needs to be different")
        assert ckeyOriginal!=obj.getContentKey()
        key3,new,changed=self.osisclient.set(obj)
        print("check 3nd save new & changed are False,True for modified obj")
        assert new==False
        assert changed==True
        print("key should be same")
        assert key==key3

        obj3=self.osisclient.get(key3)
        print("guid should be same even after content change")
        assert obj3.guid==key
        
        print("verify id structure")
        testresult = self.verify_id(key)
        assert testresult==True


    def test_set_and_self(self):
        numbers = list(range(10))
        items = self.client.list("system", "fake4test")
        startnr = len(items)
        for i in numbers:
            obj = self.osisclient.new()
            obj.name = "%s_%s" % (self.prefix, i)
            obj.netaddr = {self.randomMAC(): ['127.0.0.1', '127.0.0.2']}
            key, new, changed = self.osisclient.set(obj)
        items = self.client.list("system", "fake4test")
        assert len(items)== startnr + 10

    def test_set_and_delete(self):
        obj = self.osisclient.new()
        obj.name = "%s_1" % self.prefix
        obj.netaddr = {self.randomMAC(): ['127.0.0.1', '127.0.0.2']}
        key, new, changed = self.osisclient.set(obj)
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
